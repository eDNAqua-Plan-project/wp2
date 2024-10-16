# Where aquatic environmental DNA archives fits

There is much overlap between resources in the eDNA space. Fortunately the eDNA archives are some of the least complex parts of this.

Figure: An example dataflow showing where the eDNA archives fit


```mermaid
flowchart TD
      start("Sample Collectors"):::startclass -->first("Metadata and Data Collation"):::startclass
            geo["Sample collection geographical features"]:::startclass-->first
      expt["Sequence experiment related"]:::startclass-->first
      first-- seq submission -->INSDC[("ENA/NCBI/DDBJ sequence+metadata")]:::ednaclass
      INSDC-- fish mitochondria -->Mitofish[("MitoFish")]:::ednaclass
      INSDC-- 18S rDNA -->Eukbank:::ednaclass
      INSDC-- 18S rDNA -->PR2[("PR2")]:::ednaclass
      INSDC-- MetaGenome Analysis -->MGNify[("MGNify")]:::analysis
      INSDC-- Biodiversity: general -->GBIF[("GBIF")]:::general_obs_class
      first-- seq submission + biodiversity reference -->OBIS[("OBIS")]:::aquatic_obs_class
      INSDC-- Biodiversity: oceanic -->OBIS:::aquaticclass
      first-- Biodiversity: general -->BOLD[("BOLD: Barcode of Life")]:::ednaclass
      BOLD-->GBIF
      BOLD-- automated -->INSDC

      ReferenceLibraries-.->BOLD
      ReferenceLibraries-.->OBIS
      ReferenceLibraries-.->GBIF

      subgraph ReferenceLibraries
        BOLD
        PR2
        Mitofish
      end

      subgraph Legend
        direction LR
        m("metadata input"):::startclass
        d("mainly DNA/eDNA"):::ednaclass
        oOBS("mainly general observational"):::general_obs_class
        oAQOBS("mainly aquatic observational"):::aquatic_obs_class
        a("metagenome analysis"):::analysis
        
      end
      
      classDef startclass fill:#66ff99
      classDef analysis fill:#f96
      classDef aquatic_obs_class fill:#66ccff
      classDef general_obs_class fill:#11aabb
      classDef ednaclass fill:#909040
      linkStyle 13 stroke:red
```