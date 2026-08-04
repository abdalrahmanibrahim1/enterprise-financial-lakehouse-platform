
def build_lake_object_key(layer, source_system, entity_name, batch_id, filename):
    object_key = [
        layer,
        source_system,
        entity_name,
        f"batch_id={batch_id}",
        filename,
    ]
    
    result = "/".join(str(element) for element in object_key)

    return result

if __name__ == "__main__":
    result = build_lake_object_key(
        "landing",
        "card_processor",
        "transactions",
        "20260804_135700",
        "transactions.csv",
    )

    print (result)


    