from typing import List

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from climatemaps.datasets import DataType

app = FastAPI()

app.mount("/static/", StaticFiles(directory="website/"), name="data")


data_types = [
    DataType.model_precipitation_5m_2021_2040,
    DataType.model_precipitation_10m_2021_2040,
]


@app.get("/data_types", response_model=List[DataType])
def get_data_types():
    return data_types
