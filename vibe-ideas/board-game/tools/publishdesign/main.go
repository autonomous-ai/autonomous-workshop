// publishdesign — put ONE finished board-game project on Panda Social as a
// DRAFT design, and keep it up to date afterwards.
//
//	publishdesign -zip <archive.zip> -owner <hex> [-content c.json]   # first import
//	publishdesign -design <id> -owner <hex> -zip <archive.zip>        # new version of the files
//	publishdesign -design <id> -owner <hex> -content c.json           # rewrite the product page
//
// This is a thin wrapper over services.ImportDesign / ImportDesignVersion —
// the very calls that back POST /designs/import and its version endpoint.
// Everything that makes an imported design correct (the versioned CDN snapshot
// + _tree.json, the viewer GLB, thumbnails under <prefix>/thumbnails/<design>/,
// the design_history row, root_id, the unique slug) is the backend's code, not
// ours. Re-implementing that half is how the text2cad importer ended up
// inserting designs with a zero root_id and a history status that contradicted
// the design's own.
//
// -content carries the curated product page: the use_case section, the
// story_blocks array, and the print_specs strip (models/design_content.go).
// For a board game that is where the RULES go — the description field caps out
// long before a full rulebook, and story blocks are the section the detail page
// renders for exactly this. Every block is validated by the backend's own
// models.ValidateDesignContent before anything is written, so a block outside
// the FE's rune window fails here instead of silently not rendering.
//
// Config comes from the BACKEND's .env: config.Load() runs godotenv.Load() on
// the working directory, so run this with the panda-social-backend checkout as
// cwd (publish.py does). GCS credentials come from GOOGLE_APPLICATION_CREDENTIALS.
//
// The design lands as status=draft — private to its owner. Flipping it public
// is a human action in the app. This binary never publishes anything publicly.
package main

import (
	"context"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"strings"
	"time"

	"pandasocial/internal/config"
	"pandasocial/models"
	"pandasocial/pkg/store"
	"pandasocial/services"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

// importTimeout bounds the whole ingest. A 40MB, 350-file board game uploads
// its snapshot object by object (8 at a time), so the ceiling is generous.
const importTimeout = 30 * time.Minute

// dryCoverURL stands in for the cover the import has not uploaded yet, so a
// dry run validates the use_case section against the same rules as a real one.
const dryCoverURL = "https://cdn.example/cover.png"

// thumbExts are the cover formats the API's own sniffing would accept.
var thumbExts = map[string]bool{".png": true, ".jpg": true, ".jpeg": true, ".webp": true}

// content is the curated product page, as publish.py writes it.
type content struct {
	UseCase     *models.UseCase     `json:"use_case"`
	StoryBlocks []models.StoryBlock `json:"story_blocks"`
	PrintSpecs  *models.PrintSpecs  `json:"print_specs"`
}

func splitList(s string) []string {
	var out []string
	for _, v := range strings.Split(s, ",") {
		if v = strings.TrimSpace(v); v != "" {
			out = append(out, v)
		}
	}
	return out
}

// readThumbs loads the cover images in the given order — index 0 becomes the
// design's primary thumbnail, so the caller's order is the display order.
func readThumbs(paths []string) ([]services.ImportThumbFile, error) {
	out := make([]services.ImportThumbFile, 0, len(paths))
	for _, p := range paths {
		ext := strings.ToLower(filepath.Ext(p))
		if !thumbExts[ext] {
			return nil, fmt.Errorf("thumb %s: unsupported extension %q (png/jpg/webp)", p, ext)
		}
		data, err := os.ReadFile(p)
		if err != nil {
			return nil, fmt.Errorf("thumb %s: %w", p, err)
		}
		if ext == ".jpeg" {
			ext = ".jpg"
		}
		out = append(out, services.ImportThumbFile{Name: filepath.Base(p), Ext: ext, Data: data})
	}
	return out, nil
}

// readContent parses the product page and checks it against the FE contract
// with `cover` standing in for an empty use_case image — the section needs one
// and the design's own cover is the honest default.
func readContent(path, cover string) (*content, error) {
	if path == "" {
		return nil, nil
	}
	raw, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var c content
	if err := json.Unmarshal(raw, &c); err != nil {
		return nil, fmt.Errorf("content %s: %w", path, err)
	}
	if c.UseCase != nil && strings.TrimSpace(c.UseCase.Image) == "" {
		c.UseCase.Image = cover
	}
	if err := models.ValidateDesignContent(c.UseCase, c.StoryBlocks, c.PrintSpecs); err != nil {
		return nil, fmt.Errorf("content %s: %w", path, err)
	}
	return &c, nil
}

// applyContent writes the product page onto an existing design. use_case and
// story_blocks go through the service (owner gate + the same validation the
// API applies); print_specs has no service write path — it is an ops-authored
// field — so it takes the documented straight-to-Mongo route, validated above.
func applyContent(ctx context.Context, svc *services.Service, owner primitive.ObjectID,
	d *models.Design, c *content) ([]string, error) {
	var done []string
	if c == nil {
		return done, nil
	}
	if c.UseCase != nil {
		label, body, image := c.UseCase.Label, c.UseCase.Body, c.UseCase.Image
		updated, err := svc.UpdateUseCase(ctx, owner, d, services.UseCasePatch{
			Label: &label, Body: &body, Image: &image})
		if err != nil {
			return done, fmt.Errorf("use_case: %w", err)
		}
		*d = *updated
		done = append(done, "use_case")
	}
	if c.StoryBlocks != nil {
		updated, err := svc.ReplaceStoryBlocks(ctx, owner, d, c.StoryBlocks)
		if err != nil {
			return done, fmt.Errorf("story_blocks: %w", err)
		}
		*d = *updated
		done = append(done, fmt.Sprintf("story_blocks(%d)", len(c.StoryBlocks)))
	}
	if c.PrintSpecs != nil {
		if err := store.UpdateFields(ctx, d, d.ID, bson.M{"print_specs": c.PrintSpecs}); err != nil {
			return done, fmt.Errorf("print_specs: %w", err)
		}
		done = append(done, "print_specs")
	}
	return done, nil
}

func result(d *models.Design, h *models.DesignHistory, applied []string) {
	out := map[string]any{
		"id":      d.ID.Hex(),
		"slug":    d.Slug,
		"title":   d.Title,
		"status":  string(d.Status),
		"applied": applied,
	}
	if h != nil {
		out["history_id"] = h.ID.Hex()
		out["history_status"] = h.Status
		out["project_url"] = h.ProjectURL
		out["snapshot_bytes"] = h.SnapshotBytes
		out["thumbnails"] = d.ThumbnailURLs
	}
	res, _ := json.Marshal(out)
	fmt.Println(string(res))
}

func main() {
	zipPath := flag.String("zip", "", "zip of the design folder (required for an import)")
	owner := flag.String("owner", "", "owner user id, 24-char hex (required)")
	designID := flag.String("design", "", "existing design id: adds a version (-zip) or rewrites the page (-content)")
	contentPath := flag.String("content", "", "json file: use_case / story_blocks / print_specs")
	title := flag.String("title", "", "design title (default: derived from the folder)")
	desc := flag.String("desc", "", "description (default: derived from spec.md)")
	prompt := flag.String("prompt", "", "originating prompt shown on the design")
	tags := flag.String("tags", "", "comma-separated tags (default: imported)")
	license := flag.String("license", "", "license type (default: CC-BY-NC-SA)")
	status := flag.String("status", "draft", "draft (private) or public")
	category := flag.String("category", "", "category slug (optional)")
	thumbs := flag.String("thumbs", "", "comma-separated local image files, cover first")
	dry := flag.Bool("dry-run", false, "validate + verify the owner, insert and upload nothing")
	flag.Parse()

	if *owner == "" {
		log.Fatal("required: -owner")
	}
	if *zipPath == "" && *contentPath == "" {
		log.Fatal("nothing to do: give -zip, -content, or both")
	}
	if *zipPath == "" && *designID == "" {
		log.Fatal("-content alone needs -design <id>")
	}
	ownerID, err := primitive.ObjectIDFromHex(*owner)
	if err != nil {
		log.Fatalf("bad -owner %q: %v", *owner, err)
	}
	var targetID primitive.ObjectID
	if *designID != "" {
		if targetID, err = primitive.ObjectIDFromHex(*designID); err != nil {
			log.Fatalf("bad -design %q: %v", *designID, err)
		}
	}
	if *status != "draft" && *status != "public" {
		log.Fatalf("bad -status %q: draft or public", *status)
	}
	var zipBytes int64
	if *zipPath != "" {
		zi, serr := os.Stat(*zipPath)
		if serr != nil {
			log.Fatalf("zip: %v", serr)
		}
		zipBytes = zi.Size()
	}
	thumbFiles, err := readThumbs(splitList(*thumbs))
	if err != nil {
		log.Fatal(err)
	}

	cfg := config.Load()
	ctx, cancel := context.WithTimeout(context.Background(), importTimeout)
	defer cancel()
	if err := store.Connect(ctx, cfg.MongoURI, cfg.DBName); err != nil {
		log.Fatalf("connect mongo (db %s): %v", cfg.DBName, err)
	}

	// A design owned by a user that does not exist is invisible: it shows no
	// author byline and never appears on that account's design list. Fail here
	// rather than leave an orphan draft nobody can find.
	var u models.User
	if err := store.FindByID(ctx, &u, ownerID); err != nil {
		log.Fatalf("owner %s not found in db %s: %v", ownerID.Hex(), cfg.DBName, err)
	}

	svc := services.New(cfg)
	if svc.Storage == nil && *zipPath != "" {
		log.Fatalf("GCS not configured (GCS_BUCKET=%q) — an import must be able to write its CDN snapshot", cfg.GCSBucket)
	}

	// An existing design supplies the real cover for the use_case section; a
	// first import has none yet, so validation uses the placeholder and the
	// real url is substituted once the import returns.
	var existing *models.Design
	cover := dryCoverURL
	if !targetID.IsZero() {
		existing = &models.Design{}
		if err := store.FindByID(ctx, existing, targetID); err != nil {
			log.Fatalf("design %s not found: %v", targetID.Hex(), err)
		}
		if existing.OwnerID != ownerID {
			log.Fatalf("design %s is owned by %s, not %s", targetID.Hex(),
				existing.OwnerID.Hex(), ownerID.Hex())
		}
		if existing.PrimaryThumbnailURL != "" {
			cover = existing.PrimaryThumbnailURL
		}
	}
	page, err := readContent(*contentPath, cover)
	if err != nil {
		log.Fatal(err)
	}

	if *dry {
		mode := "import"
		if existing != nil {
			mode = "content-only"
			if *zipPath != "" {
				mode = "new-version"
			}
		}
		info := map[string]any{
			"dry_run":    true,
			"mode":       mode,
			"owner":      ownerID.Hex(),
			"owner_name": u.Username,
			"db":         cfg.DBName,
			"bucket":     cfg.GCSBucket,
			"zip":        *zipPath,
			"zip_bytes":  zipBytes,
			"title":      *title,
			"status":     *status,
			"tags":       splitList(*tags),
			"thumbs":     *thumbs,
			// The blurb is the one field a human should read before this runs
			// for real: it is what the store page shows under the title.
			"description":  *desc,
			"prompt_chars": len(*prompt),
		}
		if existing != nil {
			info["design"] = existing.ID.Hex()
			info["design_slug"] = existing.Slug
		}
		if page != nil {
			leads := make([]string, 0, len(page.StoryBlocks))
			for _, b := range page.StoryBlocks {
				leads = append(leads, fmt.Sprintf("%s (%d)", b.Lead, len([]rune(b.Body))))
			}
			info["content_valid"] = true
			info["story_blocks"] = leads
			info["use_case"] = page.UseCase != nil
			info["print_specs"] = page.PrintSpecs != nil
		}
		out, _ := json.MarshalIndent(info, "", "  ")
		fmt.Println(string(out))
		return
	}

	var design *models.Design
	var history *models.DesignHistory
	switch {
	case existing != nil && *zipPath != "":
		outcome, verr := svc.ImportDesignVersion(ctx, ownerID, existing, services.ImportVersionInput{
			ZipPath: *zipPath, Prompt: *prompt, ThumbnailFiles: thumbFiles})
		if verr != nil {
			log.Fatalf("import version: %v", verr)
		}
		design, history = outcome.Design, outcome.History
	case existing != nil:
		design = existing
	default:
		outcome, ierr := svc.ImportDesign(ctx, ownerID, services.ImportInput{
			ZipPath:        *zipPath,
			Title:          *title,
			Description:    *desc,
			CategorySlug:   *category,
			Tags:           splitList(*tags),
			Status:         *status,
			LicenseType:    *license,
			Prompt:         *prompt,
			ThumbnailFiles: thumbFiles,
		})
		if ierr != nil {
			log.Fatalf("import: %v", ierr)
		}
		design, history = outcome.Design, outcome.History
		if page != nil && page.UseCase != nil && page.UseCase.Image == dryCoverURL {
			page.UseCase.Image = design.PrimaryThumbnailURL
		}
	}

	applied, err := applyContent(ctx, svc, ownerID, design, page)
	if err != nil {
		// The design itself is already written and correct; only the curated
		// page failed. Report both so the caller knows what to retry.
		result(design, history, applied)
		log.Fatalf("content: %v", err)
	}
	result(design, history, applied)
}
