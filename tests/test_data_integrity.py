import pandas as pd
import pytest

def test_grid_data():
    df = pd.read_csv('data/grid_timeseries.csv')
    assert not df.empty
    assert len(df.drop_duplicates(subset=['timestamp', 'zone_id'])) == len(df)
    assert 'demand_mw' in df.columns
    assert 'transmission_flow_mw' in df.columns

def test_renewable_assets():
    df = pd.read_csv('data/renewable_assets.csv')
    assert not df.empty
    assert 'asset_id' in df.columns
    assert 'zone_id' in df.columns
    assert 'capacity_kw' in df.columns

def test_grid_resources():
    df = pd.read_csv('data/grid_resources.csv')
    assert not df.empty
    assert 'resource_id' in df.columns
    assert 'resource_type' in df.columns
    assert 'zone_id' in df.columns
    assert 'available_capacity_mw' in df.columns

def test_weather():
    df = pd.read_csv('data/weather_forecast.csv')
    assert not df.empty
    assert 'forecast_timestamp' in df.columns
    assert 'zone_id' in df.columns

def test_events():
    df = pd.read_csv('data/injected_events.csv')
    assert not df.empty
    assert 'start_timestamp' in df.columns
    assert 'event_type' in df.columns
