import subprocess
import sys

import weaviate
from weaviate.embedded import EmbeddedOptions
from weaviate.util import generate_uuid5

from .base import BaseANN

class Weaviate(BaseANN):
    def __init__(self, metric, max_connections, ef_construction=500):
        self.class_name = "Vector"
        self.client = weaviate.Client(
            embedded_options=EmbeddedOptions()
        )
        self.max_connections = max_connections
        self.ef_construction = ef_construction
        self.distance = {
            "angular": "cosine",
            "euclidean": "l2-squared",
        }[metric]

    def fit(self, X):
        self.client.schema.create({
            "classes": [
                {
                    "class": self.class_name,
                    "properties": [
                        {
                            "name": "i",
                            "dataType": ["int"],
                        }
                    ],
                    "vectorIndexConfig": {
                        "distance": self.distance,
                        "efConstruction": self.ef_construction,
                        "maxConnections": self.max_connections,
                    },
                }
            ]
        })
        with self.client.batch as batch:
            batch.batch_size = 100
            for i, x in enumerate(X):
                properties = { "i": i }
                uuid = generate_uuid5(properties, self.class_name)
                self.client.batch.add_data_object(
                    data_object=properties,
                    class_name=self.class_name,
                    uuid=uuid,
                    vector=x
                )

    def set_query_arguments(self, ef):
        self.ef = ef
        schema = self.client.schema.get(self.class_name)
        schema["vectorIndexConfig"]["ef"] = ef
        self.client.schema.update_config(self.class_name, schema)

    def query(self, v, n):
        ret = (
            self.client.query
            .get(self.class_name, ["i"])
            .with_near_vector({
                "vector": v,
            })
            .with_limit(n)
            .do()
        )
        # {'data': {'Get': {'Vector': [{'i': 3618}, {'i': 8213}, {'i': 4462}, {'i': 6709}, {'i': 3975}, {'i': 3129}, {'i': 5120}, {'i': 2979}, {'i': 6319}, {'i': 3244}]}}}
        return [d["i"] for d in ret["data"]["Get"][self.class_name]]

    def __str__(self):
        return f"Weaviate(ef={self.ef}, maxConnections={self.max_connections}, efConstruction={self.ef_construction})"
