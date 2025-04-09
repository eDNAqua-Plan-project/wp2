# Field Descriptions

- ‘_id’: Unique MongoDB identifier assigned to each scientific article entry in the database;
- ‘DOI’: Digital Object Identifier of the scientific publication;
- ‘Ancestor’: Identifier of the scientific article from which content was sourced from;
- ‘Step’: Recursive depth counter indicating how many steps were taken from seed papers. A Step value of 0 indicates a seed paper, while higher values indicate papers discovered through cited references;
- ‘Q1’ - ‘Q10’: A standardized set of predefined training questions applied to each each article to extract information. See Appendix X for for detailed question definitions;
- ‘References’: List of citations extracted from the article that were recognized and processable by the LLM.
