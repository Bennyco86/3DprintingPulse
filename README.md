# Quality3Ds Daily 3D Printing News

## Latest Pulse
<!-- PULSE:START -->
### 3D PRINTING PULSE #313 - 2026-11-16

📷 POWDERBED brings an off-the-shelf LPBF controller to Formnext 2026
Danish startup POWDERBED will make its Formnext debut next week with Core 1, an off-the-shelf scanner and laser controller for laser powder bed fusion machines that ships with open-source machine control software.
The company is exhibiting on the Sensortherm stand at Formnext 2026 in Frankfurt, which runs from November 17 to 20, reported by VoxelMatters on Nov 15, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/core1-front-cutout-1672-150x150.jpg
Read more ? https://www.voxelmatters.com/powderbed-brings-an-off-the-shelf-lpbf-controller-to-formnext-2026

💻 16-year-old F3 champion designs and 3D prints a new front wing at the track
Nicolas Lenzi Loeffler, a 16-year-old racing driver from Munich, designed and 3D printed a custom front wing upgrade for his Dallara F312 Mercedes-AMG Formula 3 car and ran it at the Mugello race weekend.
The project went from a digital CAD model to a finished part on the car, and he built the base structure … The post 16-year-old F3 champion designs and 3D prints a new front wing at the track appeared first on, reported by VoxelMatters on Nov 15, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/16-year-old-F3-champion-designs-and-3D-prints-front-wing1794337957662-150x150.jpg
Read more ? https://www.voxelmatters.com/16-year-old-f3-champion-designs-and-3d-prints-a-new-front-wing-at-the-track

🖨 ABS and Radian Forge begin WAAM marine components digital testing
Classification organization ABS and Radian Forge have signed a joint development project to evaluate whether digital manufacturing data could support the qualification of metal components produced by wire arc...
The JDP was set up to examine whether manufacturing process parameters, real-time sensor data, inspection records and material testing results could provide a sound … The post ABS and Radian Forge begin WAAM marine, reported by VoxelMatters on Nov 14, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/ABS-Radian-Forge-150x150.jpeg
Read more ? https://www.voxelmatters.com/abs-and-radian-forge-begins-waam-marine-components-digital-testing

🚀 SPEE3D opens first NodeZERO factory in Darwin as start of 50-site CriticalSPEE3D network
SPEE3D has launched Phase One of NodeZERO in Darwin, the first of 50 advanced manufacturing factories the Australian company plans to set up across the Asia Pacific region under the name CriticalSPEE3D.
The network is designed to make critical metal parts at the point of consumption for gas plants, mines, ports and defense bases, reported by VoxelMatters on Nov 15, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/SPEE3D-CriticalSPEE3D-network-01-150x150.jpg
Read more ? https://www.voxelmatters.com/spee3d-opens-first-nodezero-factory-in-darwin-as-start-of-50-site-criticalspee3d-network

🚀 ATLIX and DHR Engineering bring automated metal AM concept to Formnext 2026
ATLIX and DHR Engineering will present a concept demonstration of continuous, automated metal additive manufacturing at Formnext 2026, combining the ATLIX xBUILD 3000 system with a robotic cell developed by DHR.
The setup is the first result of a collaboration between the German metal AM system provider, reported by VoxelMatters on Nov 15, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/ATLIX-and-DHR-Engineering-150x150.jpg
Read more ? https://www.voxelmatters.com/atlix-and-dhr-engineering-bring-automated-metal-am-concept-to-formnext-2026

📰 Callaway invests $15 million in titanium 3D printing facility in Texas
Callaway Golf Company (NYSE: CALY) committed $15 million to a new advanced 3D printing facility in Fort Worth, Texas.
The site will expand the golf equipment maker’s titanium R&D and manufacturing capabilities, and Callaway plans to use it to develop club designs that conventional manufacturing cannot produce, reported by VoxelMatters on Nov 14, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/cg-2026-quantum-family-price-drop-medium_desktop_1920x648_2026-11-05-e1794674928869-150x150.jpg
Read more ? https://www.voxelmatters.com/callaway-invests-15-million-in-titanium-3d-printing-facility-in-texas

🚀 FKM reports 67% productivity gain on unreleased EOS polymer platform
FKM Additive Manufacturing recorded a 67% rise in productivity on one production part after running the next generation of the EOS polymer platform ahead of its market launch, with an unveiling scheduled for Formnext.
Build time per component fell from 3 hours 10 minutes to 1 hour 54 minutes compared with the previous machine, according … The post FKM reports 67% productivity gain on unreleased EOS polymer platform appeared first, reported by VoxelMatters on Nov 14, 2026.
Image ? https://www.voxelmatters.com/wp-content/uploads/2026/11/FKM-EOS-01-150x150.jpg
Read more ? https://www.voxelmatters.com/fkm-reports-67-productivity-gain-on-unreleased-eos-polymer-platform

💻 OpticalShift to Give Color Shift Effects to 3D Printed Parts
Grayson Carpenter previously developed CMYKForge.
This software tool takes your image and transforms it into a color material extrusion 3D print, reported by 3DPrint.com on Nov 15, 2026.
Read more ? https://3dprint.com/336600/opticalshift-to-give-color-shift-effects-to-3d-printed-parts
<!-- PULSE:END -->

This repo hosts the latest Quality3Ds Daily Pulse.

## Automation Notes
- auto_daily.py skips stories with titles containing "news briefs".

- Image recovery reads embedded RSS images and article Open Graph/Twitter metadata; transient feed errors and unconditional HTTP 304 responses are retried. Google News links without publisher images can still appear without thumbnails.
- Model deduplication recognizes new alphanumeric model names (including H3C) without editing a model list. Further coverage of an already featured model is suppressed; substantive follow-ups require manual curation. Archived daily notes are retained; repeated stories are omitted from the public ten-edition feed.
- Run regression checks with `py -m unittest -v test_pulse` from this folder.
