#!/usr/bin/env python3
"""01b_fetch_overture.py - download business and service locations for the lower 48 states.

Plain-language note: pulls every shop, restaurant, office, school, church and other
place from the free Overture Maps release into one local file, keeping only the
location, the category and a confidence score. Used to find each town's commercial core.
"""
import os, subprocess, sys
import duckdb
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REL = "2026-10-21.0"
SRC = f"s3://overturemaps-us-west-2/release/{REL}/theme=places/type=place/*"
DEST = os.path.join(ROOT, "data", "raw", "overture", f"places_us48_{REL}.parquet")
c = duckdb.connect()
c.sql("INSTALL httpfs; LOAD httpfs; INSTALL spatial; LOAD spatial; SET s3_region='us-west-2';")
c.sql(f"""COPY (
  SELECT id, ST_X(geometry) lon, ST_Y(geometry) lat, basic_category,
         taxonomy.primary AS tax_primary, taxonomy.hierarchy[1] AS tax_top,
         confidence, operating_status, addresses[1].region AS region
  FROM read_parquet('{SRC}', hive_partitioning=1)
  WHERE bbox.xmin BETWEEN -125 AND -66.5 AND bbox.ymin BETWEEN 24 AND 49.5
    AND addresses[1].country = 'US'
) TO '{DEST}' (FORMAT parquet)""")
n = c.sql(f"select count(*) from '{DEST}'").fetchall()[0][0]
subprocess.run([sys.executable, os.path.join(ROOT, "tools", "provenance.py"), DEST, SRC,
                "--log", os.path.join(ROOT, "data", "raw", "PROVENANCE.txt"),
                "--note", f"DuckDB extract, lower-48 bbox, country=US, {n} rows; Overture license per source (CDLA-Permissive-2.0 / ODbL / Apache)"], check=True)
print("overture rows", n)
