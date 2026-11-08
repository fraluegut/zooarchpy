# References

Primary sources must be consulted before implementing algorithms derived from them.

**Status legend.**

- `[read]`: a maintainer has read the primary source and checked that the code matches it.
- `[record confirmed]`: the bibliographic record (authors, journal, volume, pages) was found
  in a publisher or library catalogue, but the full text has **not** been read (paywalled
  or not available online). Cited for context only.
- `[to verify]`: cited from memory; even the bibliographic details are unconfirmed.

Nothing that is not `[read]` may be implemented as a method.

## General references

- Lyman, R. L. (1994). Quantitative units and terminology in zooarchaeology. *American Antiquity*, 59(1), 36–71. doi:10.2307/3085500. [Publisher page](https://www.cambridge.org/core/journals/american-antiquity/article/quantitative-units-and-terminology-in-zooarchaeology/6DA3144CA714E705C9E5E51CD9D6FB61) (paywalled). `[record confirmed]`
- Lyman, R. L. (2008). *Quantitative Paleozoology*. Cambridge University Press. `[to verify]`
- Grayson, D. K. (1984). *Quantitative Zooarchaeology: Topics in the Analysis of Archaeological Faunas*. Academic Press. `[to verify]`
- Reitz, E. J. & Wing, E. S. (2008). *Zooarchaeology* (2nd ed.). Cambridge University Press. `[to verify]`
- Binford, L. R. (1984). *Faunal Remains from Klasies River Mouth*. Academic Press. `[to verify]`

## Fragment-based MNE and MNI (planned, Phase 2)

Background for deciding whether two fragments can belong to the same bone.

- Marean, C. W., Abe, Y., Nilssen, P. J. & Stone, E. C. (2001). Estimating the minimum number of skeletal elements (MNE) in zooarchaeology: a review and a new image-analysis GIS approach. *American Antiquity*, 66(2), 333–348. doi:10.2307/2694612. [Publisher page](https://www.cambridge.org/core/journals/american-antiquity/article/estimating-the-minimum-number-of-skeletal-elements-mne-in-zooarchaeology-a-review-and-a-new-imageanalysis-gis-approach/096279CDB7254F99175DAA920A5D3E1F) (paywalled). Its abstract distinguishes the *overlap* approach from the *fraction summation* approach to MNE and notes that procedures are rarely explicit and vary between studies. **Priority source to read before MNE.** `[record confirmed]`
- Dobney, K. & Rielly, K. (1988). A method for recording archaeological animal bones: the use of diagnostic zones. *Circaea*, 5(2), 79–96. No online copy or catalogue record found; volume and pages unconfirmed. `[to verify]`
- Watson, J. P. N. (1979). The estimation of the relative frequencies of mammalian species: Khirokitia 1972. *Journal of Archaeological Science*, 6(2), 127–137. Cited by later work as the origin of counting by diagnostic zones to avoid counting the same bone twice. `[record confirmed]`
- Klein, R. G. & Cruz-Uribe, K. (1984). *The Analysis of Animal Bones from Archaeological Sites*. University of Chicago Press. Includes a chapter on computing MNI, covering how indeterminate fragments are treated. Book; no free copy found. `[record confirmed]`
- Marean, C. W. & Spencer, L. M. (1991). Impact of carnivore ravaging on zooarchaeological measures of element abundance. *American Antiquity*, 56(4), 645–658. About carnivore effects on element counts, not about fragment matching. Relevant to limitations, not to the algorithm. `[record confirmed]`
- White, T. E. (1953). A method of calculating the dietary percentage of various food animals utilized by aboriginal peoples. *American Antiquity*, 18(4), 396–398. Credited in the literature with introducing MNI; one catalogue attributed it to different authors, so author details need checking against the original issue. `[record confirmed]`

## Critical reviews of MNI

- Lyman, R. L. (2018). A critical review of four efforts to resurrect MNI in zooarchaeology. *Journal of Archaeological Method and Theory*. [Springer](https://link.springer.com/doi/10.1007/s10816-018-9365-3). Year and volume to be confirmed. `[to verify]`
- Domínguez-Rodrigo, M. (2012). Critical review of the MNI (minimum number of individuals) as a zooarchaeological unit of quantification. *Archaeological and Anthropological Sciences*. Volume and pages to be confirmed. `[to verify]`

Zone schemes for specific taxonomic groups (mammals, birds, fish...) will be listed here
with the exact source of each scheme when they are added; the library does not invent them.

Per-method references are listed in each method's page (e.g. [nisp.md](nisp.md)).
