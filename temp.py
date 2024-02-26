


# 예시 input
input_data = [
  {'skill_experienceid': 1, 'keyword': '경험', 'search_keyword': ['경험'], 'type': None, 'sub_skill_experience_list': None, 'and_condition_list': None},
  {'skill_experienceid': 2, 'keyword': '전략', 'search_keyword': ['전략'], 'type': None, 'sub_skill_experience_list': [1], 'and_condition_list': None},
  {'skill_experienceid': 3, 'keyword': '분석', 'search_keyword': ['분석'], 'type': None, 'sub_skill_experience_list': [1, 2], 'and_condition_list': None},
  {'skill_experienceid': 4, 'keyword': '프로젝트', 'search_keyword': ['프로젝트'], 'type': None, 'sub_skill_experience_list': None, 'and_condition_list': None},
  {'skill_experienceid': 5, 'keyword': '웹 개발', 'search_keyword': ['웹', '개발'], 'type': None, 'sub_skill_experience_list': [4], 'and_condition_list': None},
  {'skill_experienceid': 6, 'keyword': '프론트엔드', 'search_keyword': ['프론트엔드'], 'type': None, 'sub_skill_experience_list': [5], 'and_condition_list': None},
  {'skill_experienceid': 7, 'keyword': '백엔드', 'search_keyword': ['백엔드'], 'type': None, 'sub_skill_experience_list': [5], 'and_condition_list': None},
  {'skill_experienceid': 8, 'keyword': 'HTML', 'search_keyword': ['HTML'], 'type': None, 'sub_skill_experience_list': [6], 'and_condition_list': None},
  {'skill_experienceid': 9, 'keyword': 'CSS', 'search_keyword': ['CSS'], 'type': None, 'sub_skill_experience_list': [6], 'and_condition_list': None},
  {'skill_experienceid': 10, 'keyword': 'JavaScript', 'search_keyword': ['JavaScript'], 'type': None, 'sub_skill_experience_list': [6], 'and_condition_list': None},
  {'skill_experienceid': 11, 'keyword': 'React', 'search_keyword': ['React'], 'type': None, 'sub_skill_experience_list': [10], 'and_condition_list': None},
  {'skill_experienceid': 12, 'keyword': 'Hooks', 'search_keyword': ['Hooks'], 'type': None, 'sub_skill_experience_list': [11], 'and_condition_list': None},
  {'skill_experienceid': 13, 'keyword': 'Redux', 'search_keyword': ['Redux'], 'type': None, 'sub_skill_experience_list': [11], 'and_condition_list': None},
  {'skill_experienceid': 14, 'keyword': 'Python', 'search_keyword': ['Python'], 'type': None, 'sub_skill_experience_list': [7], 'and_condition_list': None},
  {'skill_experienceid': 15, 'keyword': 'Django', 'search_keyword': ['Django'], 'type': None, 'sub_skill_experience_list': [14], 'and_condition_list': None},
  {'skill_experienceid': 16, 'keyword': 'ORM', 'search_keyword': ['ORM'], 'type': None, 'sub_skill_experience_list': [15], 'and_condition_list': None},
  {'skill_experienceid': 17, 'keyword': 'REST API', 'search_keyword': ['REST', 'API'], 'type': None, 'sub_skill_experience_list': [15], 'and_condition_list': None},
  {'skill_experienceid': 18, 'keyword': 'MySQL', 'search_keyword': ['MySQL'], 'type': None, 'sub_skill_experience_list': [7], 'and_condition_list': None},
  {'skill_experienceid': 19, 'keyword': 'AWS', 'search_keyword': ['AWS'], 'type': None, 'sub_skill_experience_list': [7], 'and_condition_list': None},
]
# input_data를 tree_data로 변환하는 함수
def convert_to_tree(input_data):
  # skill_experienceid를 키로 하고 나머지 정보를 값으로 하는 딕셔너리 생성
  data_dict = {item['skill_experienceid']: item for item in input_data}
  # tree_data를 담을 빈 리스트 생성
  tree_data = []
  # input_data의 각 요소에 대해 반복
  for item in input_data:
    # sub_skill_experience_list가 None이거나 비어있는 경우
    if not item['sub_skill_experience_list']:
      # label에 keyword, value에 skill_experienceid를 넣은 딕셔너리 생성
      node = {'label': item['keyword'], 'value': item['skill_experienceid'], 'search_keyword': item['search_keyword']}
      # node에 children을 추가하는 함수 호출
      add_children(node, data_dict)
      # tree_data에 추가
      tree_data.append(node)
  # tree_data를 반환
  return tree_data

# node에 children을 추가하는 함수
def add_children(node, data_dict):
  # data_dict에서 node의 skill_experienceid를 부모로 가지는 요소들을 찾음
  # data_dict[sub_id]['sub_skill_experience_list']가 None이 아닌지 확인하는 조건을 추가
  children = [data_dict[sub_id] for sub_id in data_dict if data_dict[sub_id]['sub_skill_experience_list'] and node['value'] in data_dict[sub_id]['sub_skill_experience_list']]
  # children이 비어있지 않은 경우
  if children:
    # children을 담을 빈 리스트 생성
    child_nodes = []
    # children의 각 요소에 대해 반복
    for child in children:
      # label에 keyword, value에 skill_experienceid를 넣은 딕셔너리 생성
      child_node = {'label': child['keyword'], 'value': child['skill_experienceid'], 'search_keyword': child['search_keyword']}
      # child_node에 children을 추가하는 함수 재귀적으로 호출
      add_children(child_node, data_dict)
      # child_nodes에 추가
      child_nodes.append(child_node)
    # node에 children 키와 값으로 child_nodes 리스트를 추가
    node['children'] = child_nodes

# tree_data를 필터링하는 함수
def filter_tree_data(tree_data, search_terms):
  # searched_tree_data를 담을 빈 리스트 생성
  searched_tree_data = []
  # tree_data의 각 요소에 대해 반복
  for node in tree_data:
    # node의 label이 search_terms에 포함되거나 node의 search_keyword가 search_terms와 교집합이 있는 경우
    if node['label'] in search_terms or set(node['search_keyword']) & set(search_terms):
      # node를 searched_tree_data에 추가
      searched_tree_data.append(node)
    # node의 children이 있는 경우
    elif node.get('children'):
      # node의 children을 필터링하는 함수 재귀적으로 호출
      searched_children = filter_tree_data(node['children'], search_terms)
      # searched_children이 비어있지 않은 경우
      if searched_children:
        # node의 children을 searched_children으로 바꿈
        node['children'] = searched_children
        # node를 searched_tree_data에 추가
        searched_tree_data.append(node)
  # searched_tree_data를 반환
  return searched_tree_data


# input_data를 tree_data로 변환하는 함수를 테스트
tree_data = convert_to_tree(input_data)
# tree_data를 출력
print(tree_data)

print(filter_tree_data(tree_data, ['웹']))