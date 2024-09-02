import json
import pandas as pd
import os

def json_to_csv_creator(json_path, data_path) :

    complete_data = {}
    complete_data["bug_id"] = []
    complete_data["original"] = []
    complete_data["vanilla"] = []
    complete_data["without_KASAN"] = []
    complete_data["without_KMSAN"] = []
    complete_data["SLAB_to_SLUB"] = []
    complete_data["KMSAN_to_KASAN"] = []
    complete_data["KASAN_to_KMSAN"] = []

    with open(json_path,"r") as f :
        json_data = json.load(f)

    for key, value in json_data.items() :
        complete_data["bug_id"].append(key)
        complete_data["original"].append("")
        complete_data["vanilla"].append("")
        complete_data["without_KASAN"].append("N/A")
        complete_data["without_KMSAN"].append("N/A")
        complete_data["SLAB_to_SLUB"].append("N/A")
        complete_data["KMSAN_to_KASAN"].append("N/A")
        complete_data["KASAN_to_KMSAN"].append("N/A")

        with open(os.path.join(data_path,key+".json"),"r") as f :
            orig_data = json.load(f)

        complete_data["original"][-1] = orig_data["title"]
        if value.get("vanilla") and value["vanilla"]["executed"] :
            complete_data["vanilla"][-1] = value["vanilla"]["output"]
        if value.get("without_KASAN") and value["without_KASAN"]["executed"] :
            complete_data["without_KASAN"][-1] = value["without_KASAN"]["output"]
        if value.get("without_KMSAN") and value["without_KMSAN"]["executed"] :
            complete_data["without_KMSAN"][-1] = value["without_KMSAN"]["output"]
        if value.get("SLAB_to_SLUB") and value["SLAB_to_SLUB"]["executed"] :
            complete_data["SLAB_to_SLUB"][-1] = value["SLAB_to_SLUB"]["output"]
        if value.get("KMSAN_to_KASAN") and value["KMSAN_to_KASAN"]["executed"] :
            complete_data["KMSAN_to_KASAN"][-1] = value["KMSAN_to_KASAN"]["output"]
        if value.get("KASAN_to_KMSAN") and value["KASAN_to_KMSAN"]["executed"] :
            complete_data["KASAN_to_KMSAN"][-1] = value["KASAN_to_KMSAN"]["output"]

    df = pd.DataFrame(complete_data)
    df.to_csv(os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/final_summary.csv"))

def main() :
    orig_data_path = os.getenv("FIXED_DUMP_PATH")
    json_path = os.path.join(os.getenv("EASY_EXPERIMENT_DATA_PATH"),"sublists/final_summary.json")
    json_to_csv_creator(json_path,orig_data_path)

if __name__ == '__main__' :
    main()