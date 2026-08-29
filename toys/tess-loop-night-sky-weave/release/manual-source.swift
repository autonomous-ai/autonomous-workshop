import Foundation
import CoreGraphics
import CoreText
import ImageIO

let pageW: CGFloat = 432
let pageH: CGFloat = 576

func color(_ hex: UInt32) -> CGColor {
    CGColor(red: CGFloat((hex >> 16) & 255) / 255,
            green: CGFloat((hex >> 8) & 255) / 255,
            blue: CGFloat(hex & 255) / 255,
            alpha: 1)
}

let navy = color(0x121B3A)
let ink = color(0x202A52)
let gold = color(0xE4B95F)
let moon = color(0xF7F2E6)
let coral = color(0xB84E43)
let lavender = color(0xDDD9F2)
let white = color(0xFFFFFF)

guard CommandLine.arguments.count == 5 else {
    fatalError("usage: manual-source <output.pdf> <product.png> <regular.ttf> <bold.ttf>")
}
let outputURL = URL(fileURLWithPath: CommandLine.arguments[1])
let imageURL = URL(fileURLWithPath: CommandLine.arguments[2]) as CFURL
let regularURL = URL(fileURLWithPath: CommandLine.arguments[3]) as CFURL
let boldURL = URL(fileURLWithPath: CommandLine.arguments[4]) as CFURL

for url in [regularURL, boldURL] {
    var error: Unmanaged<CFError>?
    if !CTFontManagerRegisterFontsForURL(url, .process, &error) {
        fatalError("font registration failed: \(String(describing: error?.takeRetainedValue()))")
    }
}

let regularName = "DejaVuSans" as CFString
let boldName = "DejaVuSans-Bold" as CFString
func font(_ size: CGFloat, bold: Bool = false) -> CTFont {
    CTFontCreateWithName(bold ? boldName : regularName, size, nil)
}

guard let imageSource = CGImageSourceCreateWithURL(imageURL, nil),
      let productImage = CGImageSourceCreateImageAtIndex(imageSource, 0, nil) else {
    fatalError("product image unavailable")
}

var mediaBox = CGRect(x: 0, y: 0, width: pageW, height: pageH)
let metadata: [CFString: Any] = [
    kCGPDFContextTitle: "Night-Sky Weave — In-Box Guide",
    kCGPDFContextCreator: "Autonomous Workshop",
    kCGPDFContextAuthor: "Night-Sky Weave"
]
guard let consumer = CGDataConsumer(url: outputURL as CFURL),
      let ctx = CGContext(consumer: consumer, mediaBox: &mediaBox, metadata as CFDictionary) else {
    fatalError("PDF context unavailable")
}

func rect(_ x: CGFloat, _ top: CGFloat, _ w: CGFloat, _ h: CGFloat) -> CGRect {
    CGRect(x: x, y: pageH - top - h, width: w, height: h)
}

func rounded(_ r: CGRect, _ radius: CGFloat) -> CGPath {
    CGPath(roundedRect: r, cornerWidth: radius, cornerHeight: radius, transform: nil)
}

func fill(_ r: CGRect, _ c: CGColor, radius: CGFloat = 0) {
    ctx.saveGState()
    ctx.setFillColor(c)
    ctx.addPath(radius > 0 ? rounded(r, radius) : CGPath(rect: r, transform: nil))
    ctx.fillPath()
    ctx.restoreGState()
}

func stroke(_ r: CGRect, _ c: CGColor, width: CGFloat = 1, radius: CGFloat = 0) {
    ctx.saveGState()
    ctx.setStrokeColor(c)
    ctx.setLineWidth(width)
    ctx.addPath(radius > 0 ? rounded(r, radius) : CGPath(rect: r, transform: nil))
    ctx.strokePath()
    ctx.restoreGState()
}

func paragraphStyle(_ align: CTTextAlignment = .left, leading: CGFloat = 2) -> CTParagraphStyle {
    var alignment = align
    var spacing = leading
    let settings = [
        CTParagraphStyleSetting(spec: .alignment, valueSize: MemoryLayout<CTTextAlignment>.size, value: &alignment),
        CTParagraphStyleSetting(spec: .lineSpacingAdjustment, valueSize: MemoryLayout<CGFloat>.size, value: &spacing)
    ]
    return CTParagraphStyleCreate(settings, settings.count)
}

@discardableResult
func text(_ value: String, x: CGFloat, top: CGFloat, w: CGFloat, h: CGFloat,
          size: CGFloat, c: CGColor, bold: Bool = false,
          align: CTTextAlignment = .left, leading: CGFloat = 2) -> CTFrame {
    let attrs: [NSAttributedString.Key: Any] = [
        kCTFontAttributeName as NSAttributedString.Key: font(size, bold: bold),
        kCTForegroundColorAttributeName as NSAttributedString.Key: c,
        kCTParagraphStyleAttributeName as NSAttributedString.Key: paragraphStyle(align, leading: leading)
    ]
    let attributed = NSAttributedString(string: value, attributes: attrs)
    let framesetter = CTFramesetterCreateWithAttributedString(attributed)
    let path = CGPath(rect: rect(x, top, w, h), transform: nil)
    let frame = CTFramesetterCreateFrame(framesetter, CFRange(location: 0, length: 0), path, nil)
    CTFrameDraw(frame, ctx)
    return frame
}

func line(_ x1: CGFloat, _ t1: CGFloat, _ x2: CGFloat, _ t2: CGFloat,
          c: CGColor, width: CGFloat = 2, dash: [CGFloat] = []) {
    ctx.saveGState()
    ctx.setStrokeColor(c)
    ctx.setLineWidth(width)
    ctx.setLineCap(.round)
    if !dash.isEmpty { ctx.setLineDash(phase: 0, lengths: dash) }
    ctx.move(to: CGPoint(x: x1, y: pageH - t1))
    ctx.addLine(to: CGPoint(x: x2, y: pageH - t2))
    ctx.strokePath()
    ctx.restoreGState()
}

func dot(_ x: CGFloat, _ top: CGFloat, _ radius: CGFloat, _ c: CGColor) {
    fill(rect(x - radius, top - radius, radius * 2, radius * 2), c, radius: radius)
}

func beginPage(_ background: CGColor) {
    ctx.beginPDFPage(nil)
    fill(CGRect(x: 0, y: 0, width: pageW, height: pageH), background)
}

func footer(_ page: Int, dark: Bool = false) {
    line(28, 532, 404, 532, c: dark ? lavender : ink, width: 0.6)
    text("NIGHT-SKY WEAVE", x: 28, top: 537, w: 180, h: 12, size: 7,
         c: dark ? lavender : ink, bold: true, leading: 0)
    text("\(page) / 4", x: 350, top: 537, w: 54, h: 12, size: 7,
         c: dark ? lavender : ink, bold: true, align: .right, leading: 0)
}

func sectionKicker(_ value: String, top: CGFloat, dark: Bool = false) {
    dot(30, top + 4, 3.2, dark ? gold : coral)
    text(value.uppercased(), x: 40, top: top, w: 330, h: 16, size: 7.5,
         c: dark ? gold : coral, bold: true, leading: 0)
}

func drawTile(cx: CGFloat, topCenter: CGFloat, size: CGFloat, family: String,
              rotation: CGFloat = 0, muted: Bool = false) {
    let cy = pageH - topCenter
    ctx.saveGState()
    ctx.translateBy(x: cx, y: cy)
    ctx.rotate(by: rotation)
    let tileColor = muted ? lavender : gold
    let featureColor = navy
    let tileRect = CGRect(x: -size / 2, y: -size / 2, width: size, height: size)
    ctx.setFillColor(tileColor)
    ctx.addPath(CGPath(roundedRect: tileRect, cornerWidth: size * 0.12,
                       cornerHeight: size * 0.12, transform: nil))
    ctx.fillPath()
    ctx.setStrokeColor(featureColor)
    ctx.setLineWidth(max(1.2, size * 0.035))
    ctx.setLineCap(.round)
    let gate = size * 0.22
    ctx.move(to: CGPoint(x: 0, y: size / 2)); ctx.addLine(to: CGPoint(x: 0, y: size / 2 - gate))
    ctx.move(to: CGPoint(x: 0, y: -size / 2)); ctx.addLine(to: CGPoint(x: 0, y: -size / 2 + gate))
    ctx.move(to: CGPoint(x: size / 2, y: 0)); ctx.addLine(to: CGPoint(x: size / 2 - gate, y: 0))
    ctx.move(to: CGPoint(x: -size / 2, y: 0)); ctx.addLine(to: CGPoint(x: -size / 2 + gate, y: 0))
    ctx.strokePath()

    let scale = size / 31.5
    var points: [(CGFloat, CGFloat, CGFloat)] = []
    if family == "crescent" {
        points = [(-2.8, 4.3, 1.1), (-5.1, 1.7, 1.1), (-5.1, -1.7, 1.1), (-2.8, -4.3, 1.1)]
    } else if family == "comet" {
        points = [(-3, 3, 2), (0, 0, 1.1), (2.5, -2.5, 0.9), (4.5, -4.5, 0.7)]
    } else {
        points = [(0, 0, 1.4), (0, 4.7, 1), (4.5, 1.45, 1), (2.8, -3.8, 1), (-2.8, -3.8, 1), (-4.5, 1.45, 1)]
    }
    ctx.setFillColor(featureColor)
    for (x, y, r) in points {
        ctx.fillEllipse(in: CGRect(x: x * scale - r * scale, y: y * scale - r * scale,
                                   width: r * 2 * scale, height: r * 2 * scale))
    }
    let pipCount = family == "crescent" ? 1 : (family == "comet" ? 2 : 3)
    let pipPoints: [(CGFloat, CGFloat)] = [(-10.2, -10.2), (-7, -10.2), (-10.2, -7)]
    for i in 0..<pipCount {
        let p = pipPoints[i]
        let r: CGFloat = 1.1 * scale
        ctx.fillEllipse(in: CGRect(x: p.0 * scale - r, y: p.1 * scale - r, width: r * 2, height: r * 2))
    }
    ctx.restoreGState()
}

func numberedStep(_ number: Int, title: String, body: String, top: CGFloat, dark: Bool = false) {
    let circle = dark ? gold : coral
    dot(42, top + 11, 11, circle)
    text("\(number)", x: 34, top: top + 4, w: 16, h: 16, size: 9, c: dark ? navy : white,
         bold: true, align: .center, leading: 0)
    text(title, x: 62, top: top, w: 330, h: 18, size: 10, c: dark ? moon : navy, bold: true)
    text(body, x: 62, top: top + 18, w: 330, h: 34, size: 8, c: dark ? lavender : ink, leading: 1.5)
}

// PAGE 1 — exact product visual and promise
beginPage(navy)
sectionKicker("Pocket constellation toy", top: 28, dark: true)
text("NIGHT-SKY\nWEAVE", x: 28, top: 52, w: 376, h: 100, size: 35, c: moon, bold: true, leading: -2)
text("TURN  •  FLIP  •  WEAVE", x: 31, top: 151, w: 300, h: 18, size: 9, c: gold, bold: true, leading: 0)
let imagePanel = rect(28, 182, 376, 250)
fill(imagePanel, lavender, radius: 18)
ctx.saveGState()
ctx.addPath(rounded(imagePanel, 18)); ctx.clip()
if let crop = productImage.cropping(to: CGRect(x: 65, y: 210, width: 1070, height: 750)) {
    ctx.draw(crop, in: imagePanel)
} else {
    ctx.draw(productImage, in: imagePanel)
}
ctx.restoreGState()
text("Nine reversible tiles. One shared edge gate. No fixed answer.",
     x: 38, top: 450, w: 356, h: 42, size: 13, c: moon, bold: true, align: .center, leading: 2)
fill(rect(44, 504, 344, 26), ink, radius: 13)
text("IN THE BOX  ·  3 CRESCENT  ·  3 COMET  ·  3 STAR",
     x: 54, top: 512, w: 324, h: 12, size: 6.8, c: gold, bold: true, align: .center, leading: 0)
footer(1, dark: true)
ctx.endPDFPage()

// PAGE 2 — inventory and setup
beginPage(moon)
sectionKicker("01 · Meet the sky pieces", top: 26)
text("Three families.\nNine ways to begin.", x: 28, top: 48, w: 376, h: 62, size: 23, c: navy, bold: true, leading: 0)
text("Both faces can play. Family identity survives without color: feel the center dots, then count the tiny corner pips.",
     x: 28, top: 114, w: 376, h: 38, size: 8.5, c: ink, leading: 2)

let cardTops: [CGFloat] = [160, 249, 338]
let families = [("crescent", "CRESCENT × 3", "Four dots curve like a moon. One corner pip."),
                ("comet", "COMET × 3", "Four dots trail from large to small. Two corner pips."),
                ("star", "STAR × 3", "A center dot with five orbiting dots. Three corner pips.")]
for i in 0..<3 {
    let top = cardTops[i]
    fill(rect(28, top, 376, 76), white, radius: 12)
    stroke(rect(28, top, 376, 76), lavender, width: 0.8, radius: 12)
    drawTile(cx: 72, topCenter: top + 38, size: 58, family: families[i].0)
    text(families[i].1, x: 116, top: top + 14, w: 260, h: 18, size: 10, c: navy, bold: true)
    text(families[i].2, x: 116, top: top + 35, w: 260, h: 28, size: 8, c: ink, leading: 1.5)
}

fill(rect(28, 430, 376, 102), navy, radius: 14)
text("SET UP ON A FLAT SURFACE", x: 44, top: 444, w: 330, h: 16, size: 8, c: gold, bold: true)
text("1  Place any tile face up.\n2  Add a neighbor edge-to-edge so the centered grooves meet.\n3  Rotate or flip until the line feels ready to continue.",
     x: 44, top: 465, w: 326, h: 58, size: 8.5, c: moon, leading: 4)
footer(2)
ctx.endPDFPage()

// PAGE 3 — guided first play and challenge prompts
beginPage(navy)
sectionKicker("02 · Follow one line", top: 26, dark: true)
text("Your first weave", x: 28, top: 48, w: 376, h: 38, size: 25, c: moon, bold: true)
text("Connections are loose on purpose: nudge edges together; never press, bend, or force a lock.",
     x: 28, top: 88, w: 376, h: 34, size: 8.5, c: lavender, leading: 2)

drawTile(cx: 126, topCenter: 168, size: 72, family: "star", rotation: 0)
drawTile(cx: 198, topCenter: 168, size: 72, family: "comet", rotation: .pi / 2)
drawTile(cx: 270, topCenter: 168, size: 72, family: "crescent", rotation: .pi)
dot(162, 168, 4, gold)
dot(234, 168, 4, gold)
line(90, 212, 306, 212, c: gold, width: 1, dash: [3, 4])
text("STAR ANCHOR", x: 91, top: 219, w: 70, h: 13, size: 7.2, c: gold, bold: true, align: .center)
text("COMET PATH", x: 163, top: 219, w: 70, h: 13, size: 7.2, c: gold, bold: true, align: .center)
text("CRESCENT CURL", x: 235, top: 219, w: 70, h: 13, size: 7.2, c: gold, bold: true, align: .center)

numberedStep(1, title: "Choose an anchor", body: "Start with a Star. Pick any edge gate as your first direction.", top: 248, dark: true)
numberedStep(2, title: "Carry the path", body: "Turn a Comet beside it. Let the centered grooves touch edge-to-edge.", top: 303, dark: true)
numberedStep(3, title: "Give it a character", body: "Curl a Crescent at the end. What did the three tiles become? Name it.", top: 358, dark: true)

text("THREE OPEN CHALLENGES", x: 28, top: 425, w: 376, h: 16, size: 8, c: gold, bold: true)
let challengeX: [CGFloat] = [28, 154, 280]
let challenges = [("SNOWFLAKE", "Build around a center."), ("DRAGON", "Make a stepped spine."), ("CROWN", "Find a base and peaks.")]
for i in 0..<3 {
    fill(rect(challengeX[i], 446, 116, 78), ink, radius: 10)
    text(challenges[i].0, x: challengeX[i] + 9, top: 459, w: 98, h: 14, size: 7.5, c: moon, bold: true, align: .center)
    text(challenges[i].1, x: challengeX[i] + 9, top: 481, w: 98, h: 28, size: 7, c: lavender, align: .center, leading: 1.5)
}
footer(3, dark: true)
ctx.endPDFPage()

// PAGE 4 — ambiguity, reset, care, safety
beginPage(moon)
sectionKicker("03 · Close the constellation", top: 26)
text("Reset the sky.\nKeep every star.", x: 28, top: 48, w: 376, h: 62, size: 23, c: navy, bold: true, leading: 0)

fill(rect(28, 124, 180, 180), lavender, radius: 14)
text("PACK-AWAY MOSAIC", x: 44, top: 140, w: 148, h: 16, size: 8, c: navy, bold: true, align: .center)
let small: CGFloat = 36
let gap: CGFloat = 3
let seq = ["crescent", "comet", "star", "star", "crescent", "comet", "comet", "star", "crescent"]
for i in 0..<9 {
    let row = i / 3
    let col = i % 3
    drawTile(cx: 75 + CGFloat(col) * (small + gap), topCenter: 176 + CGFloat(row) * (small + gap), size: small, family: seq[i])
}
text("Count 3 across × 3 down = all 9.", x: 42, top: 278, w: 152, h: 14, size: 7.5, c: navy, bold: true, align: .center)

text("IF THE WEAVE FEELS STUCK", x: 232, top: 126, w: 172, h: 18, size: 8, c: coral, bold: true)
text("LINE STOPS?\nRotate a quarter-turn or flip the tile.\n\nTILES DRIFT?\nUse a flat surface and nudge edges together.\n\nFAMILY UNCLEAR?\nCount corner pips: 1 Crescent, 2 Comet, 3 Star.",
     x: 232, top: 151, w: 172, h: 140, size: 7.8, c: ink, leading: 2)

fill(rect(28, 312, 376, 92), navy, radius: 14)
text("RESET IN THREE MOVES", x: 44, top: 327, w: 330, h: 16, size: 8, c: gold, bold: true)
text("1  Gather and count all nine.\n2  Make three rows of three.\n3  Place the mosaic flat; either face may be up.",
     x: 44, top: 350, w: 330, h: 48, size: 8.5, c: moon, leading: 3)

text("CARE & SAFETY", x: 28, top: 424, w: 160, h: 18, size: 9, c: coral, bold: true)
text("• Wipe with a lightly damp cloth, then dry before storing. Do not soak.\n• Keep away from high heat and open flame.\n• Small parts: keep away from children under 3 and anyone who mouths objects.\n• Before play, count all nine and inspect them. Set aside any cracked piece or sharp edge.\n• If a piece is missing, stop and find it before packing away.",
     x: 28, top: 447, w: 376, h: 75, size: 8, c: ink, leading: 1.8)
footer(4)
ctx.endPDFPage()

ctx.closePDF()
