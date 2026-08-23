// importdesign — local-only ingestion CLI for the panda-social backend.
//
// Source of truth lives in the text2cad repo (integrations/importdesign/);
// build.sh copies it into a local checkout of panda-social-backend to compile
// against the pandasocial module. By policy it is NEVER committed to the
// backend repo — the pipeline stays inside the VM (Tam 2026-08-11).
//
// Inserts ONE design with status=draft (private) + its DesignHistory row, via
// the same services layer seedmock uses, so slugs/invariants hold. A human
// flips draft->public in admindash — that flip is the publish confirmation.
package main

import (
	"context"
	crand "crypto/rand"
	"encoding/hex"
	"encoding/json"
	"flag"
	"fmt"
	"log"
	"strings"
	"time"

	"pandasocial/internal/config"
	"pandasocial/models"
	"pandasocial/pkg/store"
	"pandasocial/services"

	"go.mongodb.org/mongo-driver/bson"
	"go.mongodb.org/mongo-driver/bson/primitive"
)

func randHex(n int) string {
	b := make([]byte, n/2)
	_, _ = crand.Read(b)
	return hex.EncodeToString(b)
}

func main() {
	title := flag.String("title", "", "design title (required)")
	desc := flag.String("desc", "", "description (required)")
	owner := flag.String("owner", "", "owner user id, 24-char hex (required)")
	thumbs := flag.String("thumbs", "", "comma-separated CDN image URLs; first = primary (required)")
	prompt := flag.String("prompt", "", "generation prompt for design history")
	projectURL := flag.String("project-url", "", "CDN project dir URL (optional; derived if empty)")
	license := flag.String("license", "CC-BY-NC", "license type")
	tags := flag.String("tags", "", "comma-separated tags")
	dry := flag.Bool("dry-run", false, "validate + print, insert nothing")
	flag.Parse()

	if *title == "" || *desc == "" || *owner == "" || *thumbs == "" {
		log.Fatal("required: -title -desc -owner -thumbs")
	}
	ownerID, err := primitive.ObjectIDFromHex(*owner)
	if err != nil {
		log.Fatalf("bad -owner %q: %v", *owner, err)
	}
	var thumbURLs []string
	for _, t := range strings.Split(*thumbs, ",") {
		if t = strings.TrimSpace(t); t != "" {
			thumbURLs = append(thumbURLs, t)
		}
	}
	var tagList []string
	for _, t := range strings.Split(*tags, ",") {
		if t = strings.TrimSpace(t); t != "" {
			tagList = append(tagList, t)
		}
	}

	design := &models.Design{
		OwnerID:             ownerID,
		Title:               *title,
		Description:         *desc,
		Tags:                tagList,
		Status:              models.StatusDraft, // private until a human flips it in admindash
		Tier:                models.TierStlAsset,
		Origin:              models.OriginImport,
		ThumbnailURLs:       thumbURLs,
		PrimaryThumbnailURL: thumbURLs[0],
		Branch:              "main",
		License:             models.License{Type: *license},
	}

	if *dry {
		out, _ := json.MarshalIndent(design, "", "  ")
		fmt.Printf("DRY-RUN, would insert:\n%s\n", out)
		return
	}

	cfg := config.Load()
	ctx := context.Background()
	if err := store.Connect(ctx, cfg.MongoURI, cfg.DBName); err != nil {
		log.Fatalf("connect mongo (%s / %s): %v", cfg.MongoURI, cfg.DBName, err)
	}
	var u models.User
	if err := store.FindByID(ctx, &u, ownerID); err != nil {
		log.Printf("⚠ owner %s not found — design will have no author byline", *owner)
	}
	if err := services.InsertWithUniqueSlug(ctx, design, *title); err != nil {
		log.Fatalf("create design: %v", err)
	}

	pu := *projectURL
	if pu == "" {
		pu = "https://cdn.autonomous.ai/panda-social/" + design.ID.Hex() + "/" +
			time.Now().Format("020106") + "/" + randHex(32) + "/"
	}
	hist := &models.DesignHistory{
		DesignID:        design.ID,
		Prompt:          *prompt,
		Status:          models.HistoryStatusPublished,
		ProjectURL:      pu,
		GenerationJobID: primitive.NewObjectID(),
		CommitSha:       randHex(40),
		SchemaVersion:   models.GenerationJobSchemaVersion,
	}
	if err := store.Create(ctx, hist); err != nil {
		log.Fatalf("create design_history: %v", err)
	}
	// Link the head the same way services/import.go does (CurrentHistoryID:
	// &history.ID) — without it displayHistoryID resolves nil and the design
	// shows no version anywhere (terminal-cursor-pen-holder, 2026-08-12).
	if err := store.UpdateFields(ctx, design, design.ID, bson.M{"current_history_id": hist.ID}); err != nil {
		log.Fatalf("link current_history_id: %v", err)
	}

	out, _ := json.Marshal(map[string]string{
		"id": design.ID.Hex(), "slug": design.Slug, "status": string(design.Status),
		"project_url": pu,
	})
	fmt.Println(string(out))
}
