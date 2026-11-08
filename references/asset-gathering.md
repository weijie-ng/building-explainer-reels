# Asset gathering

How every shot gets its visual (SKILL.md, "Asset gathering", and Workflow step 4). Read it before gathering anything. The verifier checks the choices and the asset log against this file (D4, C7).

Every shot gets its visual this way, except the diagram, the map, the timeline and the end card. Those are not a way around it: use the diagram only for the one chain of links, the map once, and the timeline once, just before the end card. Gathering has two parts: a search that always runs in full, then a choice that takes judgment.

**1. Search every place, for every shot.** Before choosing, look in all four places and note what each gave:
- **A. Cited articles.** Each article's lead image (og:image) and its inline photos or charts. A page-text fetch lists the page's image URLs.
- **B. Other coverage and free images.** Reputable outlets or agencies covering the same story, and Wikimedia Commons (how-to below).
- **C. The primary source.** The post, statement or page itself, for a screenshot cropped to the claim (see "Screenshots").
- **D. Footage.** A real clip of the people, place or event, if one can be cleanly obtained (SKILL.md, "Real clips"). For the hook, look for footage first.

A find counts only when it is **related**: it shows the people, organisations, products, places, documents or data the shot is about. A stock "hacker in a hoodie", an unrelated archive photo, or a logo shot reused from another story is not related. An archive photo of the people involved is related, but never present it as the event itself.

**2. Choose.** This is a judgment, not a fixed order. Put the best related find next to what a Muse AI image or video could show, and ask which makes this shot's line clearer and more watchable.
- **Keep the real find** when the line rests on it as evidence: the false post or material, a statement or denial, or the document, chart, person or place behind a claim facts.md marks as alleged or disputed. Keep it, too, when it shows something the viewer couldn't otherwise picture. Never swap that evidence for AI because it looks dull. Give it motion instead: `push`, `pan`, `inset`, or a tighter keep box on the detail that matters.
- **Use Muse AI** in four cases:
  - the line is a concept, a process or a scale (money frozen, a queue paused, a message spreading across thousands of accounts);
  - nothing related was found;
  - the related find is still dull after a tighter crop and motion: a reused logo, a stock-looking photo, a small or blurry image, a plain head shot already used, or the same subject as the shots around it;
  - the line states a claim facts.md marks as confirmed and undisputed (an event every source agrees happened: a supply cut, a plant closure, a product launch) and its real find is a still (a photo, graphic or chart). An AI video acting out the line may replace the still; log the still you passed over. The video shows a generic scene (a terminal, not that terminal), never something that could pass as footage of the event. A real clip of the event still beats AI.

  Make AI material a video by default: an AI still is only the start frame you check and then animate (SKILL.md, "AI material", and `references/ai-video.md`). An AI still left still is the weakest moving shot there is, so log why video didn't work. See "AI material" in SKILL.md for the limits.
- **A figure is a stat shot.** When a line lands on one sourced figure (a score, a count, a date, "0 of 5"), show it as a `stat` rather than a picture: it arrives on the word and carries its source label.
- **Weigh trust.** Viewers trust a labelled AI visual less, even when it is accurate. So don't use AI where a real image carries the line just as well.
- **Headline card**, only when no real find works and AI can't show the line. It is the weakest shot (a headline on plain blue); at most 2 per reel, not counting the end card.

**3. Check the reel as a whole.**
- Something on screen changes every 2–6s: a cut, a move, a highlight, or a node or graphic build.
- Shot types take turns. Never three similar images in a row, no subject in more than two shots, and no two text screenshots back to back.
- If most shots show one logo, look for photos of the people, places or objects in the story instead.
- Run the dry run and read its pace report (SKILL.md, "Play as a video, not a slideshow") before generating or capturing anything more: it is far cheaper to swap a planned still for a clip or a stat now than after the build.

**4. Log it.** For each shot, add a row to the **asset log** in facts.md with four entries:
- the shot;
- what each of A–D gave (or "nothing related");
- what was chosen;
- why, in a few words, for example "B: Reuters photo of the minister, the receipt" or "A: only the logo, already used twice; AI: frozen funds".

Record each asset's file, source, date and licence there too. The verifier checks this log (D4, C7).

**When an image has too much text (fails D5), repair it before dropping it.** Stop at the first step that works:
1. Re-crop the keep box to the photo, chart or logo, or to the account name plus the one or two claim lines (about 25 words).
2. Use the same article's lead image, or an inline photo or chart.
3. Use another source's image, or a shorter post stating the same claim.
4. Use AI.
5. Use a headline card, only after steps 1–4. Note each attempt in the asset log.

**Downloading and checking images.**
- **Download as JPEG or PNG.** Image CDNs pick the format from the request, so a `.png` URL can return AVIF or WebP, which the build can't read. Send `Accept: image/jpeg`, or change `f_auto` to `f_jpg` in Cloudinary-style URLs.
- **Wikimedia Commons.** Search with `commons.wikimedia.org/w/api.php?action=query&list=search&srnamespace=6&srsearch=…`, then read each file's licence, author and date. Download either the original file URL or the `thumburl` the API returns with `prop=imageinfo&iiurlwidth=1280`. Commons rejects thumbnail sizes it didn't generate (HTTP 400).
- **Credit the photo on screen** with photographer, year and licence (for example "PHOTO: GAGE SKIDMORE, 2025, CC BY-SA 3.0"), or "IMAGE: OUTLET, DATE" for an article's image. A concept or stock photo is labelled "ILLUSTRATIVE PHOTO".
- **Check what each photo shows.** Crop out anything now false, such as an old job title on a slide behind the person. A photo of a person next to a claim must not suggest they made it unless they did, so name whose statement it is in the source label.
- **Look at every image and clip before it goes in the manifest.** The build rejects an image it can't read or that is almost blank.

**Screenshots.** When you use a screenshot of the actual source (the X post, the company statement, the article page), follow these capture rules:
- **The claim must be visible in the screenshot.** Posts cut off with "Show more" often hide the very line you need; use another post that states it in full, or choose again (see "2. Choose" above).
- **Times must match the labels.** Capture with the browser set to UTC (or the time zone the reel uses), because posts show times in the viewer's time zone. X posts can be captured without logging in from `platform.twitter.com/embed/Tweet.html?id=<post id>&theme=dark`.
- **Crop out what isn't the source:** ads, cookie banners, site menus. Set a keep box on the part that carries the claim.
- **Wait for images before a screenshot.** Article images often load only when scrolled into view. Scroll each one into view and wait until it has loaded, or the capture shows grey boxes.
- **Re-read the page when you capture it.** Pages change: a headline figure updated between research and capture is a fact to update in facts.md, not a detail to ignore.
- **Never put a screenshot under a headline or line it doesn't support.** An analyst's headline naming a culprit doesn't belong under a line stating it as fact.
- **Little to no text on screen besides the headline and caption.** The headline and caption already carry the claim, so the visual behind them should be an image to look at, not a page to read. Prefer a photo, logo, chart or graphic. When a screenshot is the receipt, crop the image itself to the account name plus the one or two lines that state the claim (about 25 words at most). Never show a whole post, a paragraph, or several posts.
- **No screen jumps.** At most one text screenshot per beat, and never two text screenshots back to back; put a photo, graphic or diagram between them. Several fast cuts between text-heavy frames make the screen jump and are unreadable.

A plain article photo or thumbnail is shown with outlet and date; it is not a screenshot of the page, so don't call it one.

## Platform: who gathers what

How the work is split depends on the platform:
- **Helper agents.** If the platform can start them, they can run the web searches, read page text (which lists a page's image URLs) and download images (for example with `curl`). That lets the search be shared out. Each helper looks at what it downloads and reports back its asset log rows.
- **Screenshots need a live browser that can save an image file.** So does anything that needs clicking, scrolling or a set time zone, because a page fetch returns text and image URLs, not a rendered page. An agent with such a browser captures every screenshot: X posts and article pages. A downloaded article image is not a substitute for a page screenshot. Seeing the page is not enough: the build needs the file.
- **Ask for the file, not the capture.** When the browser is a separate agent or worker, it may take the screenshot for its own checking and send back only a text description, because files flow into it by default, not back out. So every screenshot request names the deliverable: the image file itself, returned to your workspace (or saved to the platform's shared file storage) under a filename you give, cropped to what the shot must show. A description of the page is not a screenshot. When the reply comes back, check the file exists and look at it before logging it.
- **Before relying on the browser**, test it once with one such file request on any page. If it returns no file, ask again more explicitly (as a file or artifact, or saved to shared storage under a name), and try any other route the platform offers (an element or full-page capture, or a page saved as PDF and rendered to PNG) before giving up.
- **If no agent has a live browser**, ask the user for the screenshots.
- **The end-card pointer needs no browser.** It is a link preview the build draws. `scripts/fetch_preview.py <article url>` reads the page's own metadata and downloads its share image with a plain fetch (SKILL.md, "End card").
