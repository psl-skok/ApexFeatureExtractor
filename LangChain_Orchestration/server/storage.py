# server/storage.py
from __future__ import annotations
from typing import Dict, Any, List
from dataclasses import dataclass, field
import uuid
import pandas as pd
from sqlalchemy import create_engine, Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import IntegrityError
import os
import shutil
from datetime import datetime
import json

Base = declarative_base()

class Dataset(Base):
    __tablename__ = 'datasets'
    id = Column(String, primary_key=True)
    original_filename = Column(String)
    file_path = Column(String)
    num_rows = Column(Integer)
    created_at = Column(DateTime)

class Analysis(Base):
    __tablename__ = 'analyses'
    id = Column(String, primary_key=True)
    dataset_id = Column(String, ForeignKey('datasets.id'))
    status = Column(String)
    execution_log = Column(Text)  # JSON string
    artifacts = Column(Text)  # JSON string with paths
    error = Column(Text)
    created_at = Column(DateTime)
    finished_at = Column(DateTime)

class SavedGraph(Base):
    __tablename__ = 'saved_graphs'
    id = Column(String, primary_key=True)
    name = Column(String)
    graph_json = Column(Text)  # JSON string of path array
    created_at = Column(DateTime)

# DB setup (absolute, safe paths)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
DB_PATH = os.path.join(DATA_DIR, "app.db")

engine = create_engine(f"sqlite:///{DB_PATH}")
Session = sessionmaker(bind=engine)

def init_db():
    os.makedirs(os.path.join(DATA_DIR, 'datasets'), exist_ok=True)
    os.makedirs(os.path.join(DATA_DIR, 'artifacts'), exist_ok=True)
    Base.metadata.create_all(engine)

def new_id(prefix):
    return f"{prefix}_{uuid.uuid4().hex[:8]}"

def save_dataset(upload_file, original_filename):
    init_db()
    ds_id = new_id('ds')
    target_path = os.path.join(DATA_DIR, "datasets", f"{ds_id}.csv")
    with open(target_path, 'wb') as f:
        shutil.copyfileobj(upload_file.file, f)
    # Compute num_rows
    df = pd.read_csv(target_path)
    num_rows = len(df)
    with Session() as session:
        ds = Dataset(id=ds_id, original_filename=original_filename, file_path=target_path, num_rows=num_rows, created_at=datetime.now())
        session.add(ds)
        session.commit()
    return ds_id

def delete_dataset_record(dataset_id: str):
    """
    Delete a dataset record and its associated file from disk.
    """
    init_db()
    with Session() as session:
        ds = session.query(Dataset).filter_by(id=dataset_id).first()
        if not ds:
            raise KeyError(f"Dataset {dataset_id} not found")

        # Delete the CSV file if it exists
        if ds.file_path and os.path.exists(ds.file_path):
            os.remove(ds.file_path)
            print(f"✅ Deleted dataset file: {ds.file_path}")
        else:
            print(f"⚠️ File for dataset {dataset_id} not found on disk")

        # Delete associated analyses (optional cleanup)
        analyses = session.query(Analysis).filter_by(dataset_id=dataset_id).all()
        for a in analyses:
            session.delete(a)

        # Delete the dataset record
        session.delete(ds)
        session.commit()
        print(f"🗑️ Deleted dataset record from database: {dataset_id}")


def get_datasets(with_heads=False):
    init_db()
    with Session() as session:
        datasets = session.query(Dataset).all()
        result = []
        for ds in datasets:
            info = {'id': ds.id, 'original_filename': ds.original_filename, 'num_rows': ds.num_rows, 'created_at': ds.created_at.isoformat()}
            if with_heads:
                print(f"Reading file: {ds.file_path}")
                head_df = pd.read_csv(ds.file_path, nrows=10)
                info['head'] = head_df.to_dict(orient='records')
            result.append(info)
        return result

def get_dataset_df(ds_id):
    init_db()
    with Session() as session:
        ds = session.query(Dataset).filter_by(id=ds_id).first()
        if not ds:
            raise KeyError(f"Dataset {ds_id} not found")
        return pd.read_csv(ds.file_path)

def create_analysis(dataset_id):
    init_db()
    analysis_id = new_id('analysis')
    with Session() as session:
        analysis = Analysis(id=analysis_id, dataset_id=dataset_id, status='queued', created_at=datetime.now())
        session.add(analysis)
        session.commit()
    return analysis_id

def update_analysis(analysis_id, **kwargs):
    init_db()
    with Session() as session:
        analysis = session.query(Analysis).filter_by(id=analysis_id).first()
        if not analysis:
            raise KeyError(f"Analysis {analysis_id} not found")
        for k, v in kwargs.items():
            if k in ['execution_log', 'artifacts']:
                v = json.dumps(v) if v else None
            setattr(analysis, k, v)
        if 'status' in kwargs and kwargs['status'] in ['completed', 'failed']:
            analysis.finished_at = datetime.now()
        session.commit()

def get_analyses():
    init_db()
    with Session() as session:
        analyses = session.query(Analysis).all()
        return [{'id': a.id,
                'dataset_id': a.dataset_id, 
                'status': a.status, 
                'execution_log': json.loads(a.execution_log) if a.execution_log else [],
                'created_at': a.created_at.isoformat() if a.created_at else None,
                'finished_at': a.finished_at.isoformat() if a.finished_at else None
                } 
                for a in analyses
            ]

def get_analysis(analysis_id):
    init_db()
    with Session() as session:
        a = session.query(Analysis).filter_by(id=analysis_id).first()
        if not a:
            raise KeyError(f"Analysis {analysis_id} not found")
        result = {
            'id': a.id, 'dataset_id': a.dataset_id, 'status': a.status,
            'execution_log': json.loads(a.execution_log) if a.execution_log else [],
            'artifacts': json.loads(a.artifacts) if a.artifacts else {},
            'error': a.error, 'created_at': a.created_at.isoformat(),
            'finished_at': a.finished_at.isoformat() if a.finished_at else None
        }
        return result
def save_graph(name: str, graph: List[Dict[str, Any]]) -> str:
    init_db()
    graph_id = new_id('graph')
    graph_str = json.dumps(graph)
    with Session() as session:
        sg = SavedGraph(id=graph_id, name=name, graph_json=graph_str, created_at=datetime.now())
        session.add(sg)
        session.commit()
    return graph_id

def get_saved_graph(graph_id: str) -> Dict[str, Any]:
    init_db()
    with Session() as session:
        sg = session.query(SavedGraph).filter_by(id=graph_id).first()
        if not sg:
            raise KeyError(f"Graph {graph_id} not found")
        try:
            path = json.loads(sg.graph_json)
        except json.JSONDecodeError:
            raise ValueError("Invalid graph data")
        return {
            'id': sg.id,
            'name': sg.name,
            'path': path,
            'created_at': sg.created_at.isoformat()
        }

def get_saved_graphs() -> List[Dict[str, Any]]:
    init_db()
    with Session() as session:
        saved_graphs = session.query(SavedGraph).all()
        return [{'id': sg.id, 'name': sg.name} for sg in saved_graphs]