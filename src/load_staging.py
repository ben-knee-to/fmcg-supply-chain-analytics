from pathlib import Path
import csv, io, os
from dotenv import load_dotenv
import psycopg
import pandas as pd
ROOT=Path(__file__).resolve().parents[1]
CSV=ROOT/'data/analytics/warehouse_fact_staging.csv'

def validate(path=CSV):
    df=pd.read_csv(path)
    if len(df)!=25000: raise ValueError(f'Expected 25000 rows, found {len(df)}')
    if df['Ware_house_ID'].isna().any() or df['Ware_house_ID'].duplicated().any():
        raise ValueError('Warehouse IDs must be non-null and unique')
    if df['product_wg_ton'].isna().any() or (df['product_wg_ton']<0).any():
        raise ValueError('Invalid shipment weights')
    return df

def main():
    validate()
    load_dotenv(ROOT/'.env')
    conn_args={k:os.environ[v] for k,v in [('host','PGHOST'),('port','PGPORT'),('dbname','PGDATABASE'),('user','PGUSER'),('password','PGPASSWORD')]}
    with psycopg.connect(**conn_args) as conn:
        with conn.cursor() as cur:
            cur.execute('TRUNCATE staging.warehouse_raw')
            with CSV.open('r',encoding='utf-8-sig',newline='') as f:
                reader=csv.reader(f)
                header=next(reader)
                # The SQL staging table uses precisely these case-sensitive columns.
                expected=[r[0] for r in cur.execute("""SELECT column_name FROM information_schema.columns
                   WHERE table_schema='staging' AND table_name='warehouse_raw'
                   ORDER BY ordinal_position""").fetchall()]
                if header!=expected: raise ValueError(f'CSV headers differ from SQL schema: {header} vs {expected}')
                quoted=','.join('"'+x.replace('"','""')+'"' for x in header)
                with cur.copy(f'COPY staging.warehouse_raw ({quoted}) FROM STDIN WITH (FORMAT CSV, HEADER FALSE)') as cp:
                    for line in f:
                        cp.write(line.encode('utf-8'))
            cur.execute('SELECT COUNT(*), SUM("product_wg_ton") FROM staging.warehouse_raw')
            count,total=cur.fetchone()
            if count!=25000 or int(total)!=552565823: raise ValueError(f'Unexpected staging totals {count} / {total}')
            print(f'Loaded {count:,} records; shipment weight sum {total:,}')
            
if __name__=='__main__': main()

