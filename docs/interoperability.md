# Genetic Reference Libraries and Taxonomic Identification of Samples

eDNA needs to be identified. This is typically done via the genetic reference libraries by sequence similarity(e.g. blast), sequence composition(e.g. Bayes classifiers) or phylogeny


Figure: An example dataflow showing how eDNA taxonomy is identified

```mermaid
flowchart TD
      subgraph "Genetic Reference Libraries"
      ref_lib1:::startclass -->first("taxonomic entity"):::taxonomyclass
      ref_lib2:::startclass -->first("taxonomic entity")
      ref_lib3:::startclass -->first("taxonomic entity")
      first-->taxonomicDB:::taxonomyclass
      first-->taxonomicRank:::taxonomyclass
      end
      
      subgraph Taxonomic Identifications in Sample
      sample("sample"):::aquaticclass-->sequencing
      sequencing-->seq_bioinformatics_workflow:::wfclass
      seq_bioinformatics_workflow-->search_sequence:::wfclass
      seq_bioinformatics_workflow-->search_sequence
      seq_bioinformatics_workflow-->search_sequence
      subgraph tax_assignment_bioinformatics workflow
      search_sequence<-- "do the assignment" -->first
      search_sequence-->taxonomic_assignment:::taxonomyclass
      taxonomic_assignment-->taxonomic_confidence:::taxonomyclass
      end
      classDef startclass fill:#66ff99
      classDef taxonomyclass fill:#f542f2
      classDef aquaticclass fill:#66ccff
      classDef wfclass fill:#f5b642
      end
```