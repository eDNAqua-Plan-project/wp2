# Filtering of aquatic records for ENA environmental DNA

A course filtering for environmental DNA related samples was already done.

A series of tests were performed to determine whether the readrun records were associated with the aquatic environment. 

## Tags
The tax_tag’s for <span style="color:blue">tax_marine, tax_brackish</span>, tax_terrestrial and <span style="color:blue">tax_freshwater</span> are derived from the WoRMS environment assignments. 

The geo_tag’s for <span style="color:blue">geo_marine, geo_brackish</span>, geo_terrestrial and <span style="color:blue">geo_freshwater</span> are calculated if the longitude and latitude of the sample collection coordinates are within certain polygons in shapefiles. 
Aquatic is called where at least one of the tags is from an aquatic environment and the majority of tags are aquatic.

## Bias
There is bias towards finding marine rather than freshwater for three main reasons: 1) precision is needed for a lat/lon coordinate to be located in freshwater shapefiles, so challenging besides very large lakes or rivers 2) oceans and seas are often recorded in a country name metadata, other regions less so 3) WoRMS is focused on marine. The biome(broad_scale_environmental_context) field is particularly useful for freshwater though. 

Figure: Filtering the “environmental” records for those from an aquatic environment.


```mermaid
flowchart TD
      start("all_environmental_dataframe"):::startclass -->first("if ENA's aquatic geo or env tags"):::decisionclass
      geo["env_tag from lat/lon to aquatic shapefile"]-->first
      tax["tax_tag from WoRMS"]-->first
      first--yes-->aquatic_dataframe
      first-- no -->second("if ocean in country_name"):::decisionclass
      second--yes-->aquatic_dataframe
      second-- no -->third("if aquatic regex term in broad_scale_environmental_context"):::decisionclass
      third--yes-->aquatic_dataframe:::aquaticclass
      third-- no -->fourth("discarded")
      classDef startclass fill:#66ff99
      classDef decisionclass fill:#f96
      classDef aquaticclass fill:#66ccff
```
