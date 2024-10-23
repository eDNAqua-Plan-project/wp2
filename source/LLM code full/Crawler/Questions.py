class Questions:
    _questions = (
        'Are the data in this paper environmental? Only "yes" or "no".',
        'Are the data available in paper or supplement? Only "paper" or "suplement".',
        'What is the sample collection method?',
        'What is the DNA extraction method?',
        'What is the source of the protocol in protocols.io?',
        'What is the overall sequencing strategy used in experiment?',
        'What is the sequence analysis workflow?',
        'Where is the data stored?',
        'What is the marker name used in experiment?',
        'What is the reference database used for taxonomical identification?'
    )

    Q1 = _questions[0]
    Q2 = _questions[1]
    Q3 = _questions[2]
    Q4 = _questions[3]
    Q5 = _questions[4]
    Q6 = _questions[5]
    Q7 = _questions[6]
    Q8 = _questions[7]
    Q9 = _questions[8]
    Q10 = _questions[9]
    Q1_2 = 'Whether the sequencing data was grown in the laboratory? Only "yes" or "no".'

    def __init__(self):
        pass

    def __call__(self,index:int):
        if index.__class__ == int and index in range(1,11):
            return Questions._questions[index - 1]
        raise AttributeError(f'Attribute "index" must be integer from 1 to 10. Currently provided index is "{index}".')

    def __repr__(self):
        return "A set of questions for scientific paper."