import spacy
from spacy.tokens import DocBin


from spacy.training import Example
from spacy.util import minibatch
import random


nlp = spacy.blank("en")


if "ner" not in nlp.pipe_names:
    ner = nlp.add_pipe("ner")
else:
    ner = nlp.get_pipe("ner")

ner.add_label("PIN")
ner.add_label("CVV")


# load training data
db_train = DocBin().from_disk("./datafiles/train_v3.spacy")
train_docs = list(db_train.get_docs(nlp.vocab))

# Load development (validation) data
db_dev = DocBin().from_disk("./datafiles/val_v3.spacy")
dev_docs = list(db_dev.get_docs(nlp.vocab))


n_iter = 30  # number of epochs
optimizer = nlp.initialize()  # initialize blank model weights

for epoch in range(n_iter):
    random.shuffle(train_docs)
    losses = {}
    # minibatch training
    batches = minibatch(train_docs, size=8)
    for batch in batches:
        examples = [
            Example.from_dict(
                doc,
                {"entities": [(ent.start_char, ent.end_char, ent.label_) for ent in doc.ents]}
            ) 
            for doc in batch
        ]
        nlp.update(examples, sgd=optimizer, losses=losses)
    print(f"Epoch {epoch+1}/{n_iter}, Losses: {losses}")

# Save the trained model
nlp.to_disk("./models/pin_cvv_model_v3")
print("Model saved to ./models/pin_cvv_model_v3")