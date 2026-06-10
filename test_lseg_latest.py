import os
import sys

def test_lseg():
    print("Testing candidate Forward PE fields for S&P 500 (.SPX)...")
    import lseg.data as ld
    
    try:
        ld.open_session()
        print("LSEG session opened.")
    except Exception as e:
        print(f"Direct session open failed: {e}. Trying desktop.workspace...")
        try:
            ld.open_session(name="desktop.workspace")
            print("LSEG desktop.workspace session opened.")
        except Exception as e2:
            print(f"Failed to open LSEG session: {e2}")
            return None

    candidates = [
        "TR.PriceClose",
        "TR.Index_PE_RTRS",
        "TR.Index_PE_EST",
        "TR.Index_PE_EST_Roll12M",
        "TR.Index_PE_EST_Y1",
        "TR.Index_Forward_PE",
        "TR.Index_Fwd_PE",
        "TR.Index_ForwardPE",
        "TR.Index_FwdPE",
        "TR.Index_EST_PE_Ratio",
        "TR.Index_EST_PE"
    ]
    
    try:
        print("Querying latest data...")
        df = ld.get_data(
            universe=[".SPX"],
            fields=candidates
        )
        print("Query complete. Dataframe columns:")
        print(df.columns.tolist())
        print("\nFirst row of data:")
        print(df.iloc[0].to_dict())
        ld.close_session()
        return df
    except Exception as e:
        print(f"Query failed: {e}")
        try:
            ld.close_session()
        except:
            pass
        return None

if __name__ == "__main__":
    test_lseg()
