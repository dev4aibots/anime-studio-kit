// Apple's on-device text recognition (the Vision framework behind Live Text). Nothing leaves the Mac.
// Shared by tools/screenfollow.py, pagebeat.py and screenbeat.py (what is on the screen, and where), through tools/aie.py.
//
//   swiftc -O tools/ocr.swift -o "$AI_EDITOR_HOME/bin/ocr"    (tools/aie.py does this once, on macOS)
//   bin/ocr <image>                               → one JSON line: {"lines":[{"text","x","y","w","h","conf"}…]}
//   bin/ocr --serve                               → reads one image path per line on stdin, answers one JSON line each
//
// Lines come back in reading order (top to bottom, then left to right), boxes in pixels from the top-left.
import Foundation
import Vision
import CoreImage

struct Line: Codable { let text: String; let x: Double; let y: Double; let w: Double; let h: Double; let conf: Double }
struct Out: Codable { let lines: [Line]; let error: String? }

func read(_ path: String) -> Out {
    guard let ci = CIImage(contentsOf: URL(fileURLWithPath: path)) else { return Out(lines: [], error: "cannot read \(path)") }
    let W = Double(ci.extent.width), H = Double(ci.extent.height)
    let req = VNRecognizeTextRequest()
    req.recognitionLevel = .accurate
    req.usesLanguageCorrection = true
    do { try VNImageRequestHandler(ciImage: ci, options: [:]).perform([req]) } catch { return Out(lines: [], error: "\(error)") }
    var lines: [Line] = []
    for o in req.results ?? [] {
        guard let t = o.topCandidates(1).first else { continue }
        let b = o.boundingBox
        lines.append(Line(text: t.string, x: Double(b.minX) * W, y: (1 - Double(b.maxY)) * H, w: Double(b.width) * W, h: Double(b.height) * H, conf: Double(t.confidence)))
    }
    // Reading order: rows first (a line within half a line-height counts as the same row), then left to right.
    lines.sort { a, b in abs(a.y - b.y) < min(a.h, b.h) * 0.5 ? a.x < b.x : a.y < b.y }
    return Out(lines: lines, error: nil)
}

let enc = JSONEncoder()
func emit(_ o: Out) {
    if let d = try? enc.encode(o), let s = String(data: d, encoding: .utf8) { print(s) } else { print("{\"lines\":[]}") }
    fflush(stdout)
}

let args = CommandLine.arguments
if args.count >= 2 && args[1] == "--serve" {
    while let path = readLine() { emit(read(path.trimmingCharacters(in: .whitespaces))) }
} else if args.count >= 2 {
    emit(read(args[1]))
} else {
    FileHandle.standardError.write("usage: ocr <image> | ocr --serve\n".data(using: .utf8)!)
    exit(2)
}
