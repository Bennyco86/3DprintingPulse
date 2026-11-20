# Quality3Ds Daily 3D Printing News

## Latest Pulse
<!-- PULSE:START -->
### 3D PRINTING PULSE #318 - 2026-11-21

🖨 The Best New Desktop & Industrial 3D Printers from Formnext 2026: Toolchangers, Throughput & Technical Firsts - All3DP
The Best New Desktop & Industrial 3D Printers from Formnext 2026: Toolchangers, Throughput & Technical Firsts All3DP
Reported by Google News - 3D Printing on Nov 20, 2026.
Read more ? https://news.google.com/rss/articles/CBMiwwFBVV95cUxOVmVJMHJsX1MzbVY1TU45ZFg4S2dhbjVkc0VVRUhiS1pQQkI5NUhGR2RzQXFGblJ3RDl1NlViNDdZTllsWXY1QTRabzBkVDVwTm5jNExiVHpLX1FjdHN5MjVOUnJLdGJ1b3VvX296ZEF3NEZVdUQxXy1kNXlVSGVaUGVxZ29Xcnk1R3hMdzF1SU9RclJjLURGdHIyTFdvSUJYemJJcTBqdE42bkJxY3lfajZNekFINVNHdzMzRDR5X05zb2c?oc=5

🚨 Elegoo unveils its multi-toolhead Centauri X Ultra 3D printer at FormNext - OC3D
Elegoo unveils its multi-toolhead Centauri X Ultra 3D printer at FormNext OC3D
Reported by Google News - 3D Printing on Nov 20, 2026.
Read more ? https://news.google.com/rss/articles/CBMirAFBVV95cUxQS2h2OWd4MmVXM3RJNFRTa1ZQWURWQWlHRWZMZjNKVWViSVRtdDVLV2E3ZVZ2ZklrV1BIVUFxZkNEckE2MnI4VWxBeXNLWFdrczBTV3JwYWZLdG93UmJtR0E4X2JqQldhSGVya09YcHZMRkpLc0lKdFdvZ2ZKZGVRcGQ3ZkZOaWdhcGVobENEWWo1cC1fMUpONXpxU2ZBLVRNd0w5S0wyUktHZzBm?oc=5

💻 Freiburg researchers win €10 million ERC grant for CHiC2PRINT project
Two University of Freiburg researchers have received a Synergy Grant from the European Research Council worth €10 million ($10.9m) over six years.
The funding will support CHiC2PRINT, a project combining sustainable 3D printing with low-cost, high-performance plastics from industrial production, reported by VoxelMatters on Nov 20, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/ERC-Freiburg-funding-150x150.jpg
Read more ? https://www.voxelmatters.com/freiburg-researchers-win-e10-million-erc-grant-for-chic2print-project

♻️ Pollen AM & RHEON Labs Bring Pellet 3D Printing to Football Helmets
A couple of months ago, I wrote about why the progress made in leveraging additive manufacturing (AM) to improve the effectiveness of football helmets is so exciting.
That post also, reported by 3DPrint.com on Nov 20, 2026.
Image ? https://3dprint.com/wp-content/uploads/2026/11/Pollen-AM-Pam-Pro-with-printed-part-680x1024.jpg
Read more ? https://3dprint.com/337027/pollen-am-rheon-labs-bring-pellet-3d-printing-to-football-helmets

🖨 AMufacture doubles its HP Multi Jet Fusion capacity in the UK
UK contract manufacturer AMufacture has doubled its additive manufacturing production capacity by installing new HP Multi Jet Fusion 5620 Pro printers at its UK base in Portsmouth.
The company says the expansion makes it the UK’s leading contract manufacturer specializing in HP’s MJF technology, reported by VoxelMatters on Nov 20, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/AMufacture-HP-expansion-150x150.jpg
Read more ? https://www.voxelmatters.com/amufacture-doubles-its-hp-multi-jet-fusion-capacity-in-the-uk

🖨 EOS Presents HELIOR Triple-Laser SLS Platform at Formnext 2026: Technical Specifications and Pricing
EOS has introduced HELIOR, a large-format polymer additive manufacturing (AM) system based on selective laser sintering (SLS), at Formnext 2026 in Frankfurt.
The machine pairs three 70 W lasers with a roller recoater whose settings can be adjusted independently, reported by 3D Printing Industry on Nov 20, 2026.
Image ? https://3dprintingindustry.com/wp-content/uploads/2026/11/EOS_HELIOR_Production_Floor-150x100.jpg
Read more ? https://3dprintingindustry.com/news/eos-presents-helior-triple-laser-sls-platform-at-formnext-2026-technical-specifications-and-pricing-256919

🖨 AddUp integrates Dyndrite LPBF Pro software with FormUp metal 3D printers
Announced at Formnext, the integration of LPBF Pro will allow FormUp users to produce parts from build files created outside AddUp's own software suite for the first time.
Reported by TCT Magazine on Nov 19, 2026.
Image ? https://storage.ghost.io/c/f0/da/f0da4f6a-82b1-46cf-ab14-3cc5e6b2d473/content/images/2026/11/Dyndrite_20LPBF_20Pro_20UI_20-_20Python_20editor_20-3840x2065-.png
Read more ? https://www.tctmagazine.com/addup-integrates-dyndrite-lpbf-pro-software-with-formup-metal-3d-printers

🖨 GERG GmbH places multi-unit MACHX 450C order, Nikon SLM Solutions confirms
With these MACHX systems, GERG is said to be setting up a new department dedicated to serial production on large-format systems.
Reported by TCT Magazine on Nov 19, 2026.
Image ? https://storage.ghost.io/c/f0/da/f0da4f6a-82b1-46cf-ab14-3cc5e6b2d473/content/images/2026/11/Media--15--2-1.jpeg
Read more ? https://www.tctmagazine.com/gerg-gmbh-places-multi-unit-machx-450c-order-nikon-slm-solutions-confirms
<!-- PULSE:END -->

This repo hosts the latest Quality3Ds Daily Pulse.

## Automation Notes
- auto_daily.py skips stories with titles containing "news briefs".

- Image recovery reads embedded RSS images and article Open Graph/Twitter metadata; transient feed errors and unconditional HTTP 304 responses are retried. Google News links without publisher images can still appear without thumbnails.
- Model deduplication recognizes new alphanumeric model names (including H3C) without editing a model list. Further coverage of an already featured model is suppressed; substantive follow-ups require manual curation. Archived daily notes are retained; repeated stories are omitted from the public ten-edition feed.
- Run regression checks with `py -m unittest -v test_pulse` from this folder.
