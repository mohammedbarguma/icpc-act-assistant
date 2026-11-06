from src.ingestion import read_pdf, parse_toc, locate_sections

full_text, pages = read_pdf("data/icpc act.pdf")
toc, toc_end = parse_toc(full_text)
sections, missing = locate_sections(full_text, toc, toc_end, pages)

s7 = next(s for s in sections if s["section"] == 7)
print(f"Section 7: page {s7['page']}, {len(s7['text'])} characters\n")
print(s7["text"][:2500])

print("\n\nMissing sections and their table-of-contents titles:")
for n in missing:
    print(f"{n:>3}. {toc[n]}")