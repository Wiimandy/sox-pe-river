import lseg.data as ld

print("Connecting to LSEG Workspace...")
ld.open_session()
print("Session opened successfully.")

print("Querying raw data...")
df = ld.get_data(
    universe=[".SOX"],
    fields=[
        "TR.IndexPriceClose.date", 
        "TR.IndexPriceClose", 
        "TR.Index_PE_RTRS",
        "TR.Index_EST_PE_Roll12M"
    ],
    parameters={
        "SDate": "2006-06-01", 
        "EDate": "2026-06-01", 
        "Frq": "M"
    }
)

print("\n--- DataFrame Info ---")
print("Type:", type(df))
print("Index Type:", type(df.index))
print("Index Name:", df.index.name)
print("Index Preview:", df.index[:5].tolist())
print("Columns:", df.columns.tolist())
print("\n--- Head of DataFrame ---")
print(df.head(10))

ld.close_session()
