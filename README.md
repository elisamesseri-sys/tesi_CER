# tesi_CER
# Modellazione e ottimizzazione della gestione energetica di una Comunità Energetica Rinnovabile

Repository associato alla tesi di laurea triennale in Ingegneria Gestionale.

Il lavoro sviluppa un modello MILP per la gestione operativa di una Comunità Energetica Rinnovabile, considerando produzione fotovoltaica, domanda elettrica, sistema di accumulo e scambi con la rete.

## Implementazione

Il modello è stato implementato in Python mediante la libreria PuLP e risolto con il solver CBC.

Il repository contiene:

- `modello_CER.py`: scenario principale con 10 utenti, di cui 4 prosumer e 6 consumer;
- `modello_CER_5_prosumer_15_consumer.py`: scenario alternativo con 20 utenti, di cui 5 prosumer e 15 consumer.

## Software utilizzato

- Python 3.14.7
- PuLP 3.3.0
- CBC 2.10.3

## Risultati

I risultati principali e il confronto tra i due scenari sono discussi nel Capitolo 6 della tesi.
La cartella 'risultati' contiene i principali output numerici relativi ai due scenari analizzati.
