# bug_metadata.py
import subprocess
import os
import json
import shlex
import csv

def generate_AST(compile_cmds: list, linux_path: str, file_path: str) :
    for cmd in compile_cmds:
        cmdlet = shlex.split(cmd['command'])
        if cmdlet[-1] != file_path:
            continue
        
        cmdlet.remove('-c')
        output_pos = cmdlet.index('-o')

        former = cmdlet[:output_pos]
        latter = cmdlet[output_pos + 2:]
        
        # json version
        json_ans = None
        cmdlet_2 = former
        cmdlet_2 += ['-Xclang', '-ast-dump=json', '-fsyntax-only']
        cmdlet_2 += latter
        clang = subprocess.Popen(cmdlet_2, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=linux_path)
        out, err = clang.communicate()
        if clang.returncode != 0:
            raise Exception(f'Failed to generate AST: {str(err, "utf-8")}')
        else:
            json_ans = json.loads(str(out, 'utf-8'))
        #print( "*"*40 + "  AST JSON is Done  " + "*"*40)

        # normal string version
        string_ans = None
        cmdlet_1 = former
        cmdlet_1 += ['-Xclang', '-ast-dump', '-fsyntax-only']
        cmdlet_1 += latter
        clang = subprocess.Popen(cmdlet_1, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=linux_path)
        out, err = clang.communicate()
        if clang.returncode != 0:
            raise Exception(f'Failed to generate AST: {str(err, "utf-8")}')
        else:
            string_ans = str(out, 'utf-8')
        #print( "*"*40 + "  AST String is Done  " + "*"*40)
        
        return string_ans, json_ans
    return None, None

def get_begin_line(node) :
    ans = None
    if node.get("range",-1) != -1 :
        if node["range"].get("begin",-1) != -1 :
            if node["range"]["begin"].get("line",-1) != -1 :
                ans = node["range"]["begin"]["line"]
            elif node["range"]["begin"].get("spellingLoc",-1) != -1 :
                ans = node["range"]["begin"]["spellingLoc"]["line"]
            else :
                pass
    return ans

def get_end_line(node) :
    ans = None
    if node.get("range",-1) != -1 :
        if node["range"].get("end",-1) != -1 :
            if node["range"]["end"].get("line",-1) != -1 :
                ans = node["range"]["end"]["line"]
            elif node["range"]["end"].get("spellingLoc",-1) != -1 :
                ans = node["range"]["end"]["spellingLoc"]["line"]
            else :
                pass
    return ans

def get_function_body_lines(ast_json) :

    if ast_json.get("inner",-1) == -1 :
        return (None,None)

    func_body = None
    child_nodes = ast_json["inner"]
    for child in child_nodes :
        if child["kind"] == 'CompoundStmt' :
            func_body = child

    if func_body is None :
        return (None,None)

    begin = get_begin_line(func_body)
    end = get_end_line(func_body)
    return (begin,end)

def hasBody(node) :
    flag = False
    if node.get("inner",-1) == -1 :
        return False
    children = node["inner"]
    for child in children :
        if child["kind"] == "CompoundStmt" :
            return True
    return flag

def get_file_name(child) :
    file_name = "UNKNOWN_FILE"
    return file_name

def collect_function_declaration_and_bodies(ast_json, final_dict, id_to_file_mapping) :
    # leaf node
    if ast_json.get("inner",-1) == -1 :
        return

    # non-leaf node
    child_nodes = ast_json["inner"]

    for child in child_nodes :

        if child["kind"] == "FunctionDecl" and (not (hasBody(child))) :

            child_id = child["id"]
            previous_id = child.get("previousDecl","")
            previous_flag = (previous_id != "")

            # not sure why this ASSERT is not always True
            # assert(not previous_flag)

            file_name = get_file_name(child)

            id_to_file_mapping[child_id] = file_name

            func_name = child["name"]

            if final_dict.get(file_name,-1) == -1 :
                final_dict[file_name] = {}
            
            if final_dict[file_name].get(func_name,-1) == -1 :
                final_dict[file_name][func_name] = {}

        elif child["kind"] == "FunctionDecl" and hasBody(child) :
        
            child_id = child["id"]
            previous_id = child.get("previousDecl","")
            previous_flag = (previous_id != "")
            func_name = child["name"]

            if not previous_flag :
                # a new function not previosuly seen
                file_name = get_file_name(child)
                id_to_file_mapping[child_id] = file_name
            
                if final_dict.get(file_name,-1) == -1 :
                    final_dict[file_name] = {}
                
                if final_dict[file_name].get(func_name,-1) == -1 :
                    final_dict[file_name][func_name] = {}

            else :
                # expanded version of previously declared function
                if id_to_file_mapping.get(previous_id,-1) == -1 :
                    print("Something really wrong !!")
                    continue
                file_name = id_to_file_mapping[previous_id]
            
            # fill information
            final_dict[file_name][func_name]["function_range"] = get_function_body_lines(child)

def create_AST_dict(ast_json,bug_id) :
    final_dict = {}
    id_to_file_mapping = {}
    assert(ast_json["kind"] == "TranslationUnitDecl")
    collect_function_declaration_and_bodies(ast_json,final_dict,id_to_file_mapping)

    return final_dict

def print_function_boundaries(ast_dict,file_path,function_name) :
    if ast_dict.get(file_path, -1) != -1 :
        if ast_dict[file_path].get(function_name,-1) != -1 :
            #print("{}:{} ==> {}".format(file_path,function_name,ast_dict[file_path][function_name]))
            return ast_dict[file_path][function_name]
        else :
            #print("x"*40 + "  No Function Boundary found for {}:{}  ".format(file_path,function_name) + "x"*40)
            pass
    else:
        #file_path = "UNKNOWN_FILE"
        if ast_dict["UNKNOWN_FILE"].get(function_name,-1) != -1 :
            #print("{}:{} ==> {}".format(file_path,function_name,ast_dict["UNKNOWN_FILE"][function_name]))
            return ast_dict["UNKNOWN_FILE"][function_name]
        else :
            #print("x"*40 + "  No Function Boundary found for {}:{}  ".format(file_path,function_name) + "x"*40)
            pass
    return

def get_source_code(linux_path, file_path, start_line, end_line) :
    """ Source code in the file from 'start_line' to 'end_line'. """
    full_path = os.path.join(linux_path, file_path)
    file_text = None
    with open(full_path, "r", encoding='utf-8') as f :
        file_text = f.readlines()

    sub_file = file_text[start_line-1:end_line]
    return sub_file

def get_source_file_set(compile_cmds: list):
    src_set = set([])
    for cmd in compile_cmds:
        cmdlet = shlex.split(cmd['command'])
        src_set.add(cmdlet[-1])
    return src_set

def make_dir_for_path(output_dir: str, fpath: str):
    dirs = os.path.split(fpath)
    if len(dirs) > 1:
        os.makedirs(os.path.join(output_dir, *dirs[:-1]), exist_ok=True)
    return os.path.join(output_dir, fpath)

def generate_bug_metedata(bug_meta: dict, compile_cmds: list, linux_path: str, output_dir: str):
    bug_id = bug_meta['bug-id']

    super_ast_dict = {}
    clean_crash = bug_meta['clean-crash-traces']

    remaining_set = set([])
    code_dict = {}

    counter = 0
    total = 0

    src_set = get_source_file_set(compile_cmds)
    saved_files = []
    
    for outer in clean_crash:
        for inner_entry in outer:
            file_path = inner_entry["file"]
            func_name = inner_entry["func"]
            line_num = inner_entry["line"]

            if file_path in src_set:
                counter += 1
                total += 1

                ast_dict = None
                if super_ast_dict.get(file_path, -1) == -1:
                    # this file has not been compiled before
                    string_ans, json_ans = generate_AST(compile_cmds, linux_path, file_path)

                    if (string_ans is None) or (json_ans is None) :
                        # report_func("Failed to generate metadata for ", file_path, ":", func_name)
                        continue
                    
                    save_path = make_dir_for_path(os.path.join(output_dir, 'src'), file_path + '.ast')
                    with open(save_path, "w", encoding='utf-8') as f :
                        f.write(string_ans)
                    saved_files.append(os.path.join('src', file_path + '.ast'))

                    ast_dict = create_AST_dict(json_ans,bug_id)
                    super_ast_dict[file_path] = ast_dict
                else :
                    # the file has been compiled before
                    ast_dict = super_ast_dict[file_path]
                
                if len(remaining_set) > 0 :
                    # try solving the ".h" files first
                    remaining_list = list(remaining_set)
                    for element in remaining_list :
                        function_range = print_function_boundaries(ast_dict,element[0],element[1])
                        if (function_range is not None) :
                            if function_range.get("function_range",-1) != -1 :
                                starting_line = function_range["function_range"][0]
                                ending_line = function_range["function_range"][1]
                                source_code_entry = {}
                                source_code_entry["starting_line"] = starting_line
                                source_code_entry["ending_line"] = ending_line
                                source_code_entry["source_code"] = get_source_code(linux_path,
                                                                                    file_path,
                                                                                    starting_line,
                                                                                    ending_line)
                                code_dict[file_path+":"+func_name] = source_code_entry
                            else :
                                print("File {} : Function {} Declaration seen, but body is missing !".format(element[0],element[1]))
                    # reset the set 
                    remaining_set = set([])

                function_range = print_function_boundaries(ast_dict,file_path,func_name)
                if function_range is not None :
                    if function_range.get("function_range",-1) != -1 : 
                        starting_line = function_range["function_range"][0]
                        ending_line = function_range["function_range"][1]
                        source_code_entry = {}
                        source_code_entry["starting_line"] = starting_line
                        source_code_entry["ending_line"] = ending_line
                        source_code_entry["source_code"] = get_source_code(linux_path,
                                                                            file_path,
                                                                            starting_line,
                                                                            ending_line)
                        code_dict[file_path+":"+func_name] = source_code_entry
                    else :
                        print("File {} : Function {} Declaration seen, but body is missing !".format(file_path,func_name))

            elif ".c" in file_path[-2:] :
                total += 1
            
            elif ".h" in file_path[-2:] :
                remaining_set.add((file_path,func_name,line_num))

    with open(os.path.join(output_dir, "final_code_dict.json"), "w", encoding='utf-8') as f:
        json.dump(code_dict, f, indent=4)
    saved_files.append('final_code_dict.json')

    with open(os.path.join(output_dir, "final.csv"), "w", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["File Name", "Function Name", "Num Lines", "Calling Line"])

        for outer in clean_crash :

            for inner_entry in outer :
                file_path = inner_entry["file"]
                func_name = inner_entry["func"]
                key = file_path+":"+func_name
                if code_dict.get(key,-1) == -1 :
                    continue
                num_lines = int(code_dict[key]["ending_line"]) - int(inner_entry["line"])
                calling_line = inner_entry["line"]
                writer.writerow([file_path, func_name, num_lines, calling_line])
                # report_func("Key : {}, Num lines of code : {}, Calling Line : {}".format(key, num_lines, calling_line))
            
            writer.writerow(["", "", "", ""])
    saved_files.append('final.csv')

    # report_func("% : {}".format(counter * 100 / total))

    return saved_files
