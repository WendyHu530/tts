import random
import pandas as pd
import numpy as np
import readfile_new as f
import copy
import math
# from datetime import date
import datetime
pd.options.mode.chained_assignment = None

#####public params (Data)#####
# 1. chromosome_columns
chromosome_columns = ['No', 'Area', 'WS', 'WSG', 'D', 'W', 'E1', 'E2', 'E3', 'Footprint', 'Model_type']
# 2. Haven't assigned tools start and end No
tool_cnt_start = 430  #399
tool_cnt_end = 1100
# 3. Have assigned tools count
exist_tool_cnt = 398
# 4. Total bay count
bay_cnt = 58
# 5. Cross fab cut line
cross_fab_bay = 25
# 6. if limit scope = 1, how many bay needs ?
limit_bay_cun = 3

#####public params (Modal hyperparamters)############
# 1. gen chromosome, how many loop need to stop
assign_stop_count = 30
# 2. weight
space_efficiency_weight = 10000
relation_weight = 1
limit_weight = 5
same_floor_weight = 12
cross_floor_weight = 4
# 3. tool deviation
deviation = 250
###################################

## Gen chromosome
def gen_chromosome(toolList, currentBayList, existToolList, l_matrix, l_modal):
    _toollist = toolList
    _baylist = currentBayList
    
    limit_check = True
    while limit_check:          
        # index list
        index_list = list(range(tool_cnt_start, tool_cnt_end))
        
        # change sequence
        random_list = []
        while len(index_list) > 0:
            _pop_num = random.randrange(0, len(index_list))
            random_list.append(index_list.pop(_pop_num))
        
        #use the random sequence to map toolList and put tools into pays
        init_map = pd.DataFrame(columns=chromosome_columns)
        init_map_limit = pd.DataFrame(columns=chromosome_columns)
        for i in range(len(random_list)):
            _tool = _toollist.loc[_toollist['No'] == random_list[i]] 
            if  _tool['Model_type'].values[0] in l_modal:
                init_map_limit = init_map_limit.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
            else: 
                init_map = init_map.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
        init_chromosome = []
        init_chromosome = copy.deepcopy(existToolList)
        assign_result = assign_tool_to_bay(0, bay_cnt, True, init_map_limit, _baylist, init_chromosome, l_matrix) 
        _gen_result_chromosome = assign_tool_to_bay(0, bay_cnt, False, init_map, assign_result[1], assign_result[0], l_matrix) 
        _remain_tool = pd.concat([assign_result[2] , _gen_result_chromosome[2]])
        
        # limit_check = check_tool_limites(_gen_result_chromosome[0], l_matrix)
        limit_check = False
    
    return [_gen_result_chromosome[0], _remain_tool]

## Check limit
def check_tool_limites(generated_chromosome, l_matrix):
    out_of_limit = False
    for i in range(0, len(generated_chromosome)):
        for j in range(0, len(generated_chromosome[i])):
            i_check_start = 0
            i_check_end = 0
            if i < cross_fab_bay:
               i_check_start = 0 if (i-limit_bay_cun) < 0 else (i-limit_bay_cun)
               i_check_end = cross_fab_bay if (i+limit_bay_cun) > cross_fab_bay else (i+limit_bay_cun)
            else:
               i_check_start = cross_fab_bay if (i-limit_bay_cun) < cross_fab_bay else (i-limit_bay_cun)
               i_check_end = len(generated_chromosome) if (i+limit_bay_cun) > len(generated_chromosome) else (i+limit_bay_cun)
            if generated_chromosome[i][j]['Model_type'] != 'QQQ':
                for _i in range(i_check_start, i_check_end):
                    for _j in range(0, len(generated_chromosome[_i])):
                        if generated_chromosome[_i][_j]['Model_type'] != 'QQQ':
                            # print(generated_chromosome[i][j])
                            # print(generated_chromosome[_i][_j])
                            if l_matrix[generated_chromosome[i][j]['Model_type']][generated_chromosome[_i][_j]['Model_type']] == 0:
                                out_of_limit = True;
                                return out_of_limit
    return out_of_limit

## Assugn tool list to bay (normal)                
def assign_tool_to_bay(bay_start, bay_end, limit, tmap, bayList, tchromosome, l_matrix):
    chromosome = copy.deepcopy(tchromosome)
    tool_footprint_map = tmap
    bay = copy.deepcopy(bayList)
    stop_count = 0
    diff = 1000
    while ((len(tool_footprint_map) != 0) and (stop_count != assign_stop_count)):
        # arrange tool
        for i in range(bay_start, bay_end):
            # _bayLength = bay[i]['BayLength']
            for j in range(len(tool_footprint_map)):
                bay_df = bay[i]['BayWidth'] - ((tool_footprint_map.iloc[j]['D'] + (tool_footprint_map.iloc[j]['E3'] / 2)) - deviation)
                if bay_df < diff and bay_df > 0: # D+E3/2
                    _tooLength = tool_footprint_map.iloc[j]['W'] + (tool_footprint_map.iloc[j]['E1'] / 2) + (tool_footprint_map.iloc[j]['E2'] / 2) # W+E1/2+E2/2
                    if _tooLength < bay[i]['BayLength']:
                        if limit == True:
                            _chromosome = []
                            _chromosome = copy.deepcopy(chromosome)
                            _chromosome[i].append(tool_footprint_map.iloc[j])
                            check = check_tool_limites(_chromosome, l_matrix)
                            if check == False:
                                _testModal = tool_footprint_map.loc[tool_footprint_map['Model_type'] == tool_footprint_map.iloc[j]['Model_type']]
                                _test = _testModal.loc[_testModal['WS'] == tool_footprint_map.iloc[j]['WS']]
                                for _j in range(len(_test)):
                                    _test_tooLength = _test.iloc[_j]['W'] + (_test.iloc[_j]['E1'] / 2) + (_test.iloc[_j]['E2'] / 2) # W+E1/2+E2/2
                                    _test_tooWidth = (_test.iloc[_j]['D'] + (_test.iloc[_j]['E3'] / 2) - deviation) # D+E3/2
                                    _test_bay_dif = bay[i]['BayWidth'] - _test_tooWidth
                                    if _test_tooLength < bay[i]['BayLength'] and _test_bay_dif < diff and _test_bay_dif > 0:               
                                        chromosome[i].append(_test.iloc[_j]) #if W and D is work 
                                        bay[i]['BayLength'] -= _test_tooLength #bay Length loss a tool's Length 
                                        tool_footprint_map.drop(tool_footprint_map.loc[tool_footprint_map['No']==_test.iloc[_j]['No']].index, inplace=True) #Remove a tool
                                break
                        else:
                            # chromosome[i].append(tool_footprint_map.iloc[j]) #if W and D is work 
                            # bay[i]['BayLength'] -= _tooLength #bay Length loss a tool's Length 
                            # tool_footprint_map.drop(tool_footprint_map.loc[tool_footprint_map['No']==tool_footprint_map.iloc[j]['No']].index, inplace=True) #Remove a tool
                            # break
                            _test = tool_footprint_map.loc[tool_footprint_map['WS'] == tool_footprint_map.iloc[j]['WS']]
                            for _j in range(len(_test)):
                                    _test_tooLength = _test.iloc[_j]['W'] + (_test.iloc[_j]['E1'] / 2) + (_test.iloc[_j]['E2'] / 2) # W+E1/2+E2/2
                                    _test_tooWidth = (_test.iloc[_j]['D'] + (_test.iloc[_j]['E3'] / 2) - deviation) # D+E3/2
                                    _test_bay_dif = bay[i]['BayWidth'] - _test_tooWidth
                                    if _test_tooLength < bay[i]['BayLength'] and _test_bay_dif < diff and _test_bay_dif > 0:               
                                        chromosome[i].append(_test.iloc[_j]) #if W and D is work 
                                        bay[i]['BayLength'] -= _test_tooLength #bay Length loss a tool's Length 
                                        tool_footprint_map.drop(tool_footprint_map.loc[tool_footprint_map['No']==_test.iloc[_j]['No']].index, inplace=True) #Remove a tool
                            break
        stop_count += 1 
        if(stop_count == assign_stop_count -1):
            diff = 100000
        else:
            diff += 250
        # print(tool_footprint_map)
        # print('remain : ' + str(len(tool_footprint_map)) + ' tools')
        # print('stop_count : ' + str(stop_count) + ' counts')
        
    # if(len(tool_footprint_map) != 0):
    #     print('Not all tool has been assigned ...')
    #     print('remain : ' + str(len(tool_footprint_map)) + ' tools')
    #     print('stop_count : ' + str(stop_count) + ' counts')
    # else:
    #     print('ALL tool has been assigned !!')
    return [chromosome, bay, tool_footprint_map]

## GA : crossover
def crossover(c1, c2, method, bayList, existToolList, current_toollist_id, l_matrix ,l_modal, remain_tool, all_tool): 
    remain_tool_no = copy.deepcopy(remain_tool)
    limit_check = True
    while limit_check:      
        _range = select_range(method, bay_cnt)
        _start_line = _range[0]
        _end_line = _range[1]
        _chromosome = c1
        _chromosome2 = c2
        _chromosome_old = copy.deepcopy(c1)
        
        _cross_item_c1 = [];
        for i in range(_start_line, _end_line):
            _chromosome_old[i] = []
            _chromosome_old[i] = existToolList[i]
            for j in range(len(_chromosome[i])):
                if (_chromosome[i][j]['No'] in current_toollist_id) == False:
                    # don't move the tool had been assigned
                    _cross_item_c1.append(_chromosome[i][j]['No'])  
    
        _cross_item_c2 = []
        _cross_check = []
        for z in range(len(_cross_item_c1)):
            check = 0
            for i in range(len(_chromosome2)):
                for j in range(len(_chromosome2[i])):
                    if _chromosome2[i][j]['No'] == _cross_item_c1[z]:
                        _cross_item_c2.append([i, j, _cross_item_c1[z]])
                        _cross_check.append(_cross_item_c1[z])
                        check += 1
            if check == 0:
                if (_cross_item_c1[z] in remain_tool_no) == False:
                    # print(_cross_item_c1[z])
                    remain_tool_no = np.append(remain_tool_no, _cross_item_c1[z])
        
        _cross_item_c2.sort(key=lambda x: (x[0],x[1]))
        for i in range(len(remain_tool_no)):
            if (remain_tool_no[i] in _cross_check) == False:
                _cross_item_c2.append([999,999,remain_tool_no[i]])
            else:
                print("Warning!! Tool Double (crossover)")
                print(remain_tool_no[i])
        
        crossover_map = pd.DataFrame(columns=chromosome_columns)
        crossover_map_limit = pd.DataFrame(columns=chromosome_columns)
        for z in range(len(_cross_item_c2)):
            _tool = all_tool.loc[all_tool['No'] == _cross_item_c2[z][2]]
            if _tool['Model_type'].values[0] in l_modal:
                crossover_map_limit = crossover_map_limit.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
            else: 
                crossover_map = crossover_map.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
                                 
        assign_result = assign_tool_to_bay(_start_line, _end_line, True, crossover_map_limit, bayList, _chromosome_old, l_matrix)
        c1_crossover = assign_tool_to_bay(_start_line, _end_line, False, crossover_map, assign_result[1], assign_result[0], l_matrix)                 
        _remain_tool = pd.concat([assign_result[2] , c1_crossover[2]])
        
        # limit_check = check_tool_limites(c1_crossover[0], l_matrix)
        limit_check = False
        
    return [c1_crossover[0], _remain_tool]

## GA : mutation
def mutation(c1, method, bayList, existToolList, current_toollist_id, l_matrix ,l_modal, remain_tool, all_tool):
    limit_check = True
    while limit_check:  
        _range = select_range(method, bay_cnt)
        _start_line = _range[0]
        _end_line = _range[1]
        _chromosome = c1
        _c1_old = copy.deepcopy(c1)
        
        mutation_map = pd.DataFrame(columns=chromosome_columns)
        mutation_map_limit = pd.DataFrame(columns=chromosome_columns)
        for i in range(_end_line - 1, _start_line, -1):
            _c1_old[i] = []
            _c1_old[i] = existToolList[i]
            for j in range(len(_chromosome[i])-1, -1, -1):
                _tool = _chromosome[i][j] 
                if (_tool['No'] in current_toollist_id) == False:
                    if _tool['Model_type'] in l_modal:
                        mutation_map_limit = mutation_map_limit.append(trans_aligned_format(_tool, 0, 'List'), ignore_index=True)
                    else: 
                        mutation_map = mutation_map.append(trans_aligned_format(_tool, 0, 'List'), ignore_index=True)            
        
        for i in range(len(remain_tool)):
            _tool = all_tool.loc[all_tool['No'] == remain_tool[i]]
            _check_dobule_limit = mutation_map_limit.loc[mutation_map_limit['No'] == remain_tool[i]]
            _check_dobule = mutation_map.loc[mutation_map['No'] == remain_tool[i]]
            if(len(_check_dobule_limit) == 0 and len(_check_dobule) == 0):
                if _tool['Model_type'].values[0] in l_modal:
                    mutation_map_limit = mutation_map_limit.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
                else:
                    mutation_map = mutation_map.append(trans_aligned_format(_tool, 0, 'DataFrame'), ignore_index=True)
            else:
                print("Warning!! Limit Tool Dobule ! (mutation)")
                print(_check_dobule_limit)
                print("Warning!! Nomral Tool Dobule ! (mutation)")
                print(_check_dobule)
                
        assign_result = assign_tool_to_bay(_start_line + 1, _end_line, True, mutation_map_limit, bayList, _c1_old, l_matrix)
        c1_mutation = assign_tool_to_bay(_start_line + 1, _end_line, False, mutation_map, assign_result[1], assign_result[0], l_matrix)
        _remain_tool = pd.concat([assign_result[2] , c1_mutation[2]])
        
        # limit_check = check_tool_limites(c1_mutation[0], l_matrix)
        limit_check = False
    
    return [c1_mutation[0], _remain_tool]

## GA : fitness
def fitness(c1, r_matrix, l_matrix, a12_matrix, bayList):
    _chromosome = c1
    #generate same empty matrix with the same format
    total_space_efficiency = 0
    total_relation_scope = 0
    total_limit_scope = 0
    total_footprint = 0
    tool_cnt = 0
    remaingTool = 0
    for i in range(0, len(_chromosome)):
        bayArea = bayList[i]['BayArea']
        aBayToolArea = 0
        toolLegth = 0
        for j in range(0, len(_chromosome[i])): 
           toolLegth += (_chromosome[i][j]['W'] + (_chromosome[i][j]['E1']/2) + (_chromosome[i][j]['E2']/2))
           
           tool_cnt += 1
           # calculation relationship scope
           relation_scope = 0
           _relation_scope_same_floor = 0
           _relation_scope_other_floor = 0      
           
           # limit
           _limit_scope = 0
           i_check_start = 0
           i_check_end = 0
           
           #a1 a2
           l_30_to_a1a2 = 0
           l_50_to_a1a2 = 0
           if i < cross_fab_bay:
               i_check_start = 0 if (i-limit_bay_cun) < 0 else (i-limit_bay_cun)
               i_check_end = cross_fab_bay if (i+limit_bay_cun) > cross_fab_bay else (i+limit_bay_cun)
               
               if (_chromosome[i][j]['WSG'] in a12_matrix.index) == True:
                   l_30_to_a1a2 = a12_matrix.at[_chromosome[i][j]['WSG'],'L30']
           else:
               i_check_start = cross_fab_bay if (i-limit_bay_cun) < cross_fab_bay else (i-limit_bay_cun)
               i_check_end = len(_chromosome) if (i+limit_bay_cun) > len(_chromosome) else (i+limit_bay_cun)         
               
               if (_chromosome[i][j]['WSG'] in a12_matrix.index) == True:
                   l_50_to_a1a2 = a12_matrix.at[_chromosome[i][j]['WSG'],'L50']
                   
           for _i in range(0, len(_chromosome)):
               for _j in range(0, len(_chromosome[_i])):
                   if (pd.isnull(_chromosome[i][j]['WSG']) == False and pd.isnull(_chromosome[_i][_j]['WSG']) == False and (_chromosome[i][j]['WSG'] in r_matrix.columns) == True  and (_chromosome[_i][_j]['WSG'] in r_matrix.columns) == True):
                           if i < cross_fab_bay:
                               if _i < cross_fab_bay:
                                   _relation_scope_same_floor += r_matrix[_chromosome[i][j]['WSG']][_chromosome[_i][_j]['WSG']] 
                               else:
                                   _relation_scope_other_floor += r_matrix[_chromosome[i][j]['WSG']][_chromosome[_i][_j]['WSG']] 
                           else:
                               if _i < cross_fab_bay:
                                   _relation_scope_other_floor += r_matrix[_chromosome[i][j]['WSG']][_chromosome[_i][_j]['WSG']] 
                               else:
                                   _relation_scope_same_floor += r_matrix[_chromosome[i][j]['WSG']][_chromosome[_i][_j]['WSG']] 
                   if i_check_start <= _i and i <= i_check_end:
                       if _chromosome[i][j]['Model_type'] != 'QQQ' and _chromosome[_i][_j]['Model_type'] != 'QQQ':
                                _limit_scope += l_matrix[_chromosome[i][j]['Model_type']][_chromosome[_i][_j]['Model_type']]
                                   
           total_relation_scope += _relation_scope_same_floor * same_floor_weight + _relation_scope_other_floor * cross_floor_weight + l_30_to_a1a2 + l_50_to_a1a2
           total_limit_scope += _limit_scope
           aBayToolArea += _chromosome[i][j]['Footprint']
        remaingLength = bayList[i]['BayLength'] - toolLegth
        remaingTool += int(remaingLength/2040)
        total_space_efficiency += aBayToolArea/bayArea * 100
        total_footprint += aBayToolArea
        unAssignToolCnt = tool_cnt_end - tool_cnt - 1
        
        # if unAssignToolCnt != 0:
        #     total_relation_scope = 0
        
    # total_scope = total_space_efficiency * space_efficiency_weight + total_relation_scope
    return [total_relation_scope, ((total_footprint*10.764)/297744), remaingTool, total_limit_scope, unAssignToolCnt]

## Get exist tool as mask
def gen_mask(exist_tool, baylist):  
    init_chromosome = [[] for i in range(bay_cnt)]
    init_baylist = copy.deepcopy(bayList)
    tool_assigned_id_list = []
    for i in range(0, len(baylist)):
        _existTool = exist_tool.loc[exist_tool['Location'] == baylist[i]['BayID']]
        _init_mask = []
        _tooLength = 0
        for j in range (0, len(_existTool)):  
            tool_assigned_id_list.append(_existTool.iloc[j]['No'])
            _init_mask.append(pd.Series(trans_aligned_format(_existTool, j, 'Dict')))  
            _tooLength += _existTool.iloc[j]['W'] + (_existTool.iloc[j]['E1'] / 2) + (_existTool.iloc[j]['E2'] / 2) # W+E1/2+E2/2
            # if i == 0:
            #     print(_tooLength)
        init_chromosome[i] = _init_mask
        init_baylist[i]['BayLength'] -= _tooLength
        
    return [init_chromosome, init_baylist, tool_assigned_id_list]

## Gen ramdom cut line
def select_range(method, max_vaule):
    start_line = 0
    end_line = 0 
    if method == 'single':
        start_line = random.randrange(0, max_vaule)
        end_line = max_vaule
    elif method == 'twice':
        start_line = random.randrange(0, max_vaule)
        end_line = random.randrange(0, max_vaule)
        if start_line > end_line:
            _tmp = start_line
            start_line = end_line
            end_line = _tmp       
    return [start_line, end_line]

## Get limit modal_type value = 0 (position can than closer than 3 bays)
def get_limit_modal_type(limitMatrix):
    limit_modal_types = []
    for i in range(len(limitMatrix)):
        for j in range(len(limitMatrix.index)):
            if limitMatrix.iloc[i][j] == 0.0 and ((limitMatrix.index[j] in limit_modal_types) == False):
                limit_modal_types.append(limitMatrix.index[j])
    return limit_modal_types

## Transfer toollist as align format for assign to bay list
def trans_aligned_format(_tool, _num, _type):
    init_map = {}
    for i in range(len(chromosome_columns)):
        if _type == 'DataFrame':
            init_map[chromosome_columns[i]] = _tool[chromosome_columns[i]].values[_num]
        elif _type == 'List':
            init_map[chromosome_columns[i]] = _tool[chromosome_columns[i]]
        elif _type == 'Dict':
            init_map[chromosome_columns[i]] = _tool.iloc[_num][chromosome_columns[i]]
    return init_map
    
## Transfer Dataframe to Matrix
def trans_matrix(_pd):
    _matrix = _pd
    data = {}
    index_list = _matrix['Index'].values
    for i in range(1, len(_matrix.columns)):
        data[_matrix.columns[i]] = list(_matrix[_matrix.columns[i]].values)   
    _df = pd.DataFrame(data, index=index_list)
    
    return _df

## Transfer Dataframe to Dict
def trans_list_dict(_pd):
    _matrix = _pd
    _series = []
    for j in range(0, len(_matrix)):
        _dict = {}    
        for i in range(1, len(_matrix.columns)):
            _dict[_matrix.columns[i]] = _matrix[_matrix.columns[i]].values[j]
        _series.append(_dict)
        
    return _series

## Check KetError : nan
def isNaN(x):
    if type(x) == float:
        x = float(x)
        return math.isnan(x)
    else:
        return False

if __name__ == '__main__':
    #Get init bay and unassigned toollist
    toolList = f.read_toollistFile() #ok
    bayList = trans_list_dict(f.read_baylistFile()) #ok

    #Set new bay with exist toolllist
    existToolList = f.read_existToollistFile()  #ok
    tool_bay_init = gen_mask(existToolList, bayList) #ok
    current_mask = tool_bay_init[0] #ok
    current_bay = tool_bay_init[1] #ok
    current_tool_no = tool_bay_init[2] #ok
    
    all_toolList = pd.concat([toolList , existToolList])
    
    #Get matrix for fitniss
    relationMatrix = trans_matrix(f.read_relation_matrix()) #ok    
    limitMatrix = trans_matrix(f.read_limit_matrix()) #ok 
    a12TransferMatrix = f.read_A12_transfer_loading()
        
    # position can than closer than 3 bays
    limitModalTypeList = get_limit_modal_type(limitMatrix) #ok  
    # print(limitModalTypeList)
    
    #Start to do GA algorithm
    # GA Params hyperparamters
    population_size = 10
    random_size = 4
    crossover_probability = 0.8
    crossover_method = 'twice'
    mutation_method = 'twice'
    mutation_probability = 0.08
    termination_criteria = 50
    
    run_start = datetime.datetime.now()
    print('start time : ' + str(run_start))
    #initalize population 
    inial_population = []
    inial_population_remain = []
    for i in range(population_size):
        _gen_result = gen_chromosome(toolList, current_bay, current_mask, limitMatrix, limitModalTypeList)
        inial_population.append(_gen_result[0]) #ok
        inial_population_remain.append(_gen_result[1]['No'].values) #ok
    print(f'Init(duration) : {(datetime.datetime.now() - run_start).total_seconds()}')
    
    # for i in range(len(inial_population)):
    #     assigned_count = 0
    #     for _i in range(len(inial_population[i])):
    #         assigned_count += len(inial_population[i][_i])
    #     remain_count = tool_cnt_end - assigned_count
    #     print("C" + str(i) + ": remain tool count = " + str(remain_count))
    #     print("=======================================")    
    
    iterate = 0 
    while (iterate < termination_criteria):
        crossover_start = datetime.datetime.now()
        print("------------------------------------------") 
        print('crossover start time : ' + str(crossover_start))
        #crossover population
        crossover_population = []
        crossover_remain = []
        for i in range(len(inial_population)):
            if i % 2 == 0: # a pair chromosome with a crossover_probability
                result = select_range('single', 100)
                if result[0] / 100 <= crossover_probability: # if lower than it, then start crossover
                    c1_crossover_result = crossover(inial_population[i], inial_population[i+1], crossover_method, current_bay, current_mask, current_tool_no, limitMatrix, limitModalTypeList, inial_population_remain[i], all_toolList)
                    crossover_population.append(c1_crossover_result[0]) # OK
                    crossover_remain.append(c1_crossover_result[1]['No'].values) # OK
                    
                    c2_crossover_result = crossover(inial_population[i+1], inial_population[i], crossover_method, current_bay, current_mask, current_tool_no, limitMatrix, limitModalTypeList, inial_population_remain[i+1], all_toolList)
                    crossover_population.append(c2_crossover_result[0]) # OK
                    crossover_remain.append(c2_crossover_result[1]['No'].values) # OK
                # else :
                #     crossover_population.append(inial_population[i]) # OK
                #     crossover_remain.append(inial_population_remain[i]) # OK
                #     crossover_population.append(inial_population[i+1]) # OK
                #     crossover_remain.append(inial_population_remain[i+1]) # OK
           
        print(f'crossover(duration) : {(datetime.datetime.now() - crossover_start).total_seconds()}')
        mutation_start = datetime.datetime.now()
        print('mutation start time : ' + str(mutation_start))
        #mutation population
        mutation_population = []
        mutation_remain = []
        for i in range(len(inial_population)):
            result = select_range('single', 1000)
            if result[0] / 1000 <= mutation_probability: # a chromosome with a mutation_probability, if lower than it, then start mutation # OK
                c1_mutation_result = mutation(inial_population[i], mutation_method, current_bay, current_mask, current_tool_no, limitMatrix, limitModalTypeList, inial_population_remain[i], all_toolList)
                mutation_population.append(c1_mutation_result[0])        # OK   
                mutation_remain.append(c1_mutation_result[1]['No'].values)
            # else :
            #     mutation_population.append(inial_population[i])   # OK
                
        print(f'mutation(duration) : {(datetime.datetime.now() - mutation_start).total_seconds()}')
        fintness_start = datetime.datetime.now()
        print('fintness start time : ' + str(fintness_start))    
        # fintness
        Total_population = inial_population + crossover_population + mutation_population
        Total_remain = inial_population_remain + crossover_remain + mutation_remain
        Total_fintness = []
        Total_spaceEfficiency = []
        Total_relationShip = []
        Total_limit = []
        Total_toolCnt = []
        for i in range(len(Total_population)):
            fitness_result = fitness(Total_population[i], relationMatrix, limitMatrix, a12TransferMatrix, bayList)
            Total_fintness.append(fitness_result[0])
            Total_spaceEfficiency.append(fitness_result[1])
            Total_relationShip.append(fitness_result[2])
            Total_limit.append(fitness_result[3])
            Total_toolCnt.append(fitness_result[4])
            
        print(f'fintness(duration) : {(datetime.datetime.now() - fintness_start).total_seconds()}')
        
        # selection Top 
        top_chromosome = population_size - random_size
        top_chromosome_index = sorted(range(len(Total_fintness)), key=lambda i: Total_fintness[i], reverse=True)[:top_chromosome]

        topOne_chromosome = []
        
        # result Print
        print("=======================================")
        print("Iterate times : " + str(iterate))
        for i in range(len(top_chromosome_index)):
            topOne_chromosome.append(Total_population[top_chromosome_index[i]])
            print("C" + str(top_chromosome_index[i]) + ": unAssign tool count = " + str(Total_toolCnt[top_chromosome_index[i]]))
            print("C" + str(top_chromosome_index[i]) + ": relationShip = " + str(Total_fintness[top_chromosome_index[i]]) + " , spaceEfficiency = " + str(Total_spaceEfficiency[top_chromosome_index[i]]) + " , Remaing Tool cnt = " + str(Total_relationShip[top_chromosome_index[i]]) + " , limit = " + str(Total_limit[top_chromosome_index[i]]))
        print("=======================================")
        
        selection_start = datetime.datetime.now()
        print('selection start time : ' + str(selection_start)) 
        # top chromosome + random chromosome = next population
        next_population = []
        next_remain = []
        for i in range(len(top_chromosome_index)):
            next_population.append(Total_population[top_chromosome_index[i]])
            next_remain.append(Total_remain[top_chromosome_index[i]])
        for i in range(random_size):
            _gen_result = gen_chromosome(toolList, current_bay, current_mask, limitMatrix, limitModalTypeList)
            next_population.append(_gen_result[0])
            next_remain.append(_gen_result[1]['No'].values)
 
        # print(f'selection and gen ramdon (duration) : {(datetime.datetime.now() - selection_start).total_seconds()}')
        # print(f'end time : {datetime.datetime.now()}')
        # print("------------------------------------------") 
        
        # top1
        # pd_save_for_excel = pd.DataFrame(columns=['Bay', 'Area', 'WS', 'WSG', 'ToolLength', 'ToolFootprint', 'BayArea', 'BayLength', 'Floor', 'Tool_No'])
        # for i in range(len(topOne_chromosome[0])):
        #     for j in range(len(topOne_chromosome[0][i])):
        #         _tool = topOne_chromosome[0][i]
        #         pd_save_for_excel = pd_save_for_excel.append({
        #             'Bay': bayList[i]['BayID'],
        #             'Area' : _tool[j]['Area'],
        #             'WS' : _tool[j]['WS'],
        #             'WSG' : _tool[j]['WSG'],
        #             'ToolLength' :  _tool[j]['W'] + (_tool[j]['E1'] / 2) + (_tool[j]['E2'] / 2),
        #             'BayLength' : bayList[i]['BayLength'], 
        #             'ToolWidth' :  _tool[j]['D'] + (_tool[j]['E3'] / 2),
        #             'BayWidth' : bayList[i]['BayWidth'],  
        #             'ToolFootprint' : _tool[j]['Footprint'],
        #             'BayArea' : bayList[i]['BayArea'],
        #             'Floor' : bayList[i]['Floor'],  
        #             'Tool_No' : _tool[j]['No'],
        #             'D' : _tool[j]['D'],
        #             'W' : _tool[j]['W'],
        #             'E1' : _tool[j]['E1'],
        #             'E2' : _tool[j]['E2'],
        #             'E3' : _tool[j]['E3']
        #             },ignore_index=True)
        
        # pd_save_for_excel.to_excel(r'D:\.spyder-py3\tts\transfer_2\optimizer_tts_iter_' + str(iterate) + '.xlsx', index = False, header=True)
        
        #next iterate
        inial_population = []
        inial_population = next_population
        inial_population_remain = next_remain
        iterate += 1