# ngrok 사용법 
# ./ngrok config add-authtoken ~~
# ./ngrok http 8501

# 라이브러리를 임포트합니다.
import streamlit as st
from streamlit_tree_select import tree_select
import supabase as sp
from supabase import ClientOptions
import konlpy as kp
import os
from dotenv import load_dotenv
import time
import pandas as pd
import random
import string
# gdshortener 라이브러리를 임포트합니다.
import gdshortener

# supabase의 url과 key를 환경변수로 설정합니다.
# supabase의 클라이언트를 생성합니다.
#테스트
load_dotenv()
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_SERVICE_KEY =  os.getenv("SUPABASE_SERVICE_KEY")
client = sp.create_client(SUPABASE_URL, SUPABASE_KEY)
#배포
# client = sp.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

# 채용공고의 목록을 조회하는 함수를 정의합니다.
# 채용공고의 segment를 조회하는 함수를 정의합니다.
def get_segments():
    # segment 테이블의 name을 group by로 조회합니다.
    query = client.table("match_segment").select("name")
    # 결과를 json 형태로 받습니다.
    result = query.execute()
    # 결과에서 name만 추출하여 리스트로 반환합니다.
    segments = [row["name"] for row in result.data]
    return segments

# 채용공고의 목록을 조회하는 함수를 정의합니다.
def get_jds(segment): 
    seg_words = list(client.table("match_segment").select("words").eq("name",segment).single().execute().data["words"])
    # segment 테이블의 words라는 list가 jd의 body에 포함되었는지로 segment를 분류합니다.
    # match_jd 테이블에서 segments 리스트의 값 중 하나만 title 컬럼에 포함되어도 조회

    jds = []
    for word in seg_words:
        or_condition = ""
        or_condition += "main_work.ilike.%" + word + "%"
        or_condition += ",title.ilike.%" + word + "%"
        or_condition += ",qualification.ilike.%" + word + "%"
        or_condition += ",preference.ilike.%" + word + "%"
        query = client.table('match_jd').select('*').or_(or_condition)
        if segment == "map A : 5년차 이하 첫 팀장급":
           query = query.lte("min_year",5)
        elif segment == "map B : 글로벌 업무, 저연차":
           query = query.lte("min_year",3)
        elif segment == "map C : 미들급 퍼포먼스":
           query = query.gte("min_year",4).lte("min_year",6)
        results = query.execute().data
        for jd in results:
            if jd not in jds:
                jds.append(jd)
    return jds


# 키워드에 해당하는 예상 질문 목록을 조회하는 함수를 정의합니다.
def get_questions(keywords):
    # map 테이블에서 Search_Keyword가 키워드와 일치하는 Skill_ExperienceID와 Keyword를 조회합니다.

    map = client.table("match_map").select("*").execute().data
    map_dict = {item['skill_experienceid']: item for item in map}

    all_map = convert_to_tree(map, map_dict,False)
    searched_map = filter_tree_data(convert_to_tree(map, map_dict,False),keywords)
    new_all_map = convert_to_tree(map, map_dict,True)
    # 결과에서 Skill_ExperienceID와 Keyword만 추출하여 딕셔너리로 반환합니다.

    questions_dict = {}
    questions_dict["all_map"] = all_map.copy()
    st.session_state.all_tree_data = all_map.copy()
    questions_dict["new_all_map"] = new_all_map.copy()
    st.session_state.new_all_tree_data = new_all_map.copy()
    questions_dict["searched_map"] = searched_map.copy()
    st.session_state.tree_data = searched_map.copy()
    questions_dict["map_dict"] = map_dict.copy()

    st.session_state.questions = questions_dict
    return questions_dict



# 채용공고의 우대조건과 지원자격을 키워드로 분리하는 함수를 정의합니다.
def get_keywords(jd_require, jd_optional):
    # 각각의 문장을 형태소 분석기로 분리합니다.
    # 형태소 분석기로는 konlpy의 Okt를 사용합니다.
    okt = kp.tag.Okt()
    required_keywords = []
    optional_keywords = []
    if jd_require:
        # 우대조건의 문장을 줄바꿈으로 나눕니다.
        required_sentences = jd_require.split("\n")
        # 각 문장을 형태소 분석기로 분리하고, 명사와 영어만 키워드로 추출합니다.
        for sentence in required_sentences:
            required_keywords.extend([word for word, tag in okt.pos(sentence) if tag in ["Noun", "Alpha"]])
    if jd_optional:
        # 지원자격의 문장을 줄바꿈으로 나눕니다.
        optional_sentences = jd_optional.split("\n")
        # 각 문장을 형태소 분석기로 분리하고, 명사와 영어만 키워드로 추출합니다.
        for sentence in optional_sentences:
            optional_keywords.extend([word for word, tag in okt.pos(sentence) if tag in ["Noun", "Alpha"]])
    # 키워드들을 중복을 제거하고, 리스트로 반환합니다.
    required_keywords = list(set(required_keywords))
    optional_keywords = list(set(optional_keywords))
    return required_keywords, optional_keywords

def get_random_string(length):
    # choose from all lowercase letter
    letters = string.ascii_lowercase
    result_str = ''.join(random.choice(letters) for i in range(length))
    return result_str

# input_data를 tree_data로 변환하는 함수
st.session_state.exist_id = []
st.session_state.new_tree_zero_dict = {}
def check_already_exist(id):
    if str(id) in st.session_state.exist_id:
        return check_already_exist(str(id)+"'")
    else:
        st.session_state.exist_id.append(str(id))
        return str(id)
def check_same_id(checked):
  # 결과를 저장할 빈 리스트를 만듭니다.
  result = []
  # checked의 각 값에 대해 반복합니다.
  for value in checked:
    # value의 앞부분 숫자를 추출합니다. 예를 들어, "2''"의 경우 "2"를 추출합니다.
    # 이를 위해 value에서 ' 표시를 모두 제거합니다.
    number = value.replace("'", "")
    # exist_id의 각 값에 대해 반복합니다.
    for item in st.session_state.exist_id:
      # item의 앞부분 숫자를 추출합니다. 예를 들어, "1'"의 경우 "1"을 추출합니다.
      # 이를 위해 item에서 ' 표시를 모두 제거합니다.
      item_number = item.replace("'", "")
      # value의 앞부분 숫자와 item의 앞부분 숫자가 일치하면,
      if number == item_number:
        # item을 결과 리스트에 추가합니다.
        result.append(item)
  # 결과 리스트를 반환합니다.
  return result

tail = {"not_question":"","experience": " 경험이 있나요?", "tool": " 업무상 활용 경험이 있나요?", "document": " 문서 작성 경험이 있나요?", "sector":" 업계에서의 프로젝트 또는 업무 경험이 있나요?", "startup":" 스타트업에서 프로젝트 또는 업무 경험이 있나요?"}
def convert_to_tree(input_data, data_dict, new_tree:bool):
  # skill_experienceid를 키로 하고 나머지 정보를 값으로 하는 딕셔너리 생성
  # tree_data를 담을 빈 리스트 생성
  st.session_state.exist_id = []
  st.session_state.new_tree_zero_dict = {}
  tree_data = []
  # input_data의 각 요소에 대해 반복
  for item in input_data:
    # sub_skill_experience_list가 None이거나 비어있는 경우
    if not item['parent_skill_experience_list']:
      # label에 keyword, value에 skill_experienceid를 넣은 딕셔너리 생성
      # 어미 추가
      node = {'label': "["+item['keyword']+"]"+tail[item['type']], 'value': check_already_exist(item['skill_experienceid']), 'title':item['keyword'],'className':item['type'], 'search_keyword': item['search_keyword']}
      # node에 children을 추가하는 함수 호출
      add_children(node, data_dict, new_tree)
      # tree_data에 추가
      tree_data.append(node)
  # tree_data를 반환
  return tree_data

# node에 children을 추가하는 함수
def add_children(node, data_dict,new_tree:bool):
  # data_dict에서 node의 skill_experienceid를 부모로 가지는 요소들을 찾음
  # data_dict[sub_id]['parent_skill_experience_list']가 None이 아닌지 확인하는 조건을 추가
  children = [data_dict[sub_id] for sub_id in data_dict if data_dict[sub_id]['parent_skill_experience_list'] and int(node['value'].split("'")[0]) in data_dict[sub_id]['parent_skill_experience_list']]
  
  # children이 비어있지 않은 경우
  if children:
    # children을 담을 빈 리스트 생성
    child_nodes = []
    # children의 각 요소에 대해 반복
    for item in children:
        # label에 keyword, value에 skill_experienceid를 넣은 딕셔너리 생성
        child_node = {'label': "["+item['keyword']+"]"+tail[item['type']], 'value': check_already_exist(item['skill_experienceid']), 'title':item['keyword'],'className':item['type'], 'search_keyword': item['search_keyword']}
        # child_node에 children을 추가하는 함수 재귀적으로 호출
        add_children(child_node, data_dict, new_tree)
        # child_nodes에 추가
        child_nodes.append(child_node)
        # node에 children 키와 값으로 child_nodes 리스트를 추가
        if new_tree:
            if "--이곳에 추가--" in [item["label"] for item in child_nodes]:
               for item in child_nodes:
                  if item["label"] == "--이곳에 추가--":
                    child_nodes.remove(item)
            temp_val = check_already_exist(0)
            child_nodes.append({'label': "--이곳에 추가--", 'value': temp_val,'search_keyword':[]})
            st.session_state.new_tree_zero_dict[temp_val] = node["value"]
               
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

# 페이지의 제목을 설정합니다.
st.title("역량-경험MAP 관리 페이지")

alarmURL, step1, step2, step3, step4 = st.tabs(["외부유입 유저 가입","step1","step2","step3","step4"])
# segment를 조회하는 함수를 호출하고, 결과를 라디오 버튼으로 표시합니다.
with step1:
    segments = get_segments()
segment = step1.radio("채용공고의 segment를 선택하세요.", segments)

# 조회 버튼을 만듭니다.
# if step1.button("조회"):
# segment에 해당하는 채용공고 목록을 조회하는 함수를 호출하고, 결과를 테이블로 표시합니다.
if step1.button("조회하기"):
    jds = get_jds(segment)
    st.session_state.jds = jds
if "jds" in st.session_state:
    jds = st.session_state.jds
    step2.write("총 " + str(len(jds)) + "개의 공고가 있습니다.")
    # 테이블에서 채용공고를 선택하면, 채용공고의 자세한 내용을 보여줍니다.
    jd_option = [str(row["job_postingid"])+"//"+row["title"] for row in jds]

    # 세션 상태를 이용하여 selectbox의 값과 인덱스를 저장하고 변경합니다.
    if 'jd_id' not in st.session_state:
        st.session_state.jd_id = jd_option[0]
    if 'jd_idx' not in st.session_state:
        st.session_state.jd_idx = 0

    # 콜백 함수를 정의하여 selectbox의 값이 변경될 때마다 인덱스를 업데이트합니다.
    def update_jd_idx():
        st.session_state.jd_idx = jd_option.index(st.session_state.jd_id)

    # 버튼을 누를 때마다 selectbox의 값을 변경합니다.
    st.divider()
    col1, col2 = st.columns(2)
    if col1.button("이전 공고"):
        if st.session_state.jd_idx > 0:
            st.session_state.jd_idx -= 1
            st.session_state.jd_id = jd_option[st.session_state.jd_idx]
    if col2.button("다음 공고"):
        if st.session_state.jd_idx < len(jds) - 1:
            st.session_state.jd_idx += 1
            st.session_state.jd_id = jd_option[st.session_state.jd_idx]

    # selectbox를 생성하고, on_change 매개변수에 콜백 함수를 전달합니다.
    jd_id = step2.selectbox("채용공고를 선택하세요.", jd_option, index=st.session_state.jd_idx, key=st.session_state.jd_id, on_change=update_jd_idx)

    # selectbox에서 선택한 채용공고의 내용을 보여줍니다.
    step2.write(jds[st.session_state.jd_idx]["title"])
    step2.write(str(jds[st.session_state.jd_idx]["min_year"])+"~"+str(jds[st.session_state.jd_idx]["max_year"]))
    step2.write(jds[st.session_state.jd_idx]["location"])
    jd_require = jds[st.session_state.jd_idx]["qualification"]
    jd_optional = jds[st.session_state.jd_idx]["preference"] if jds[st.session_state.jd_idx]["preference"] is not None else "" + "\n" + jds[st.session_state.jd_idx]["main_work"] if jds[st.session_state.jd_idx]["main_work"] is not None else ""
    jd = "[필수]\n\n"+jd_require + "\n\n\n[선택]\n\n" + jd_optional
    step2.write(jd)

    highlighted_jd = jd
    step3.write(jds[st.session_state.jd_idx]["title"])
    step3.write(str(jds[st.session_state.jd_idx]["min_year"])+"~"+str(jds[st.session_state.jd_idx]["max_year"]))
    step3.write(jds[st.session_state.jd_idx]["location"])
    container = step3.container(border=True)


    # 채용공고의 우대조건과 지원자격을 키워드로 분리하는 함수를 호출하고, 결과를 리스트로 표시합니다.
    required_keywords, optional_keywords = get_keywords(jd_require, jd_optional)
    keywords = step3.multiselect("공고 검색어:", required_keywords + optional_keywords, key="keywords")
    def save_jd_map(checked):
    #    keywords, qualification_keywords, preference_keywords
        result = True
        delete_duplicated = list(set([int(item.split("'")[0]) for item in checked]))
        for this_id in delete_duplicated:
            # 검색 키워드 업데이트
            map_result = client.table("match_map").select("*").eq("skill_experienceid", this_id).single().execute().data
            if map_result["type"] != "not_question":
                search_keywords = map_result["search_keyword"]
                if not set(keywords).issubset(search_keywords):
                    update_search_keyword = client.table("match_map").update({"search_keyword":list(set(search_keywords + keywords))}).eq("skill_experienceid", this_id).execute()
                    print(update_search_keyword)
                    if "error" in update_search_keyword:
                        print(update_search_keyword["error"])
                        result = False
                # jd-map 추가
                type = ""
                if set(keywords).intersection(required_keywords):
                    # len(set(list1).intersection(list2))
                    type = "required"
                else:
                    type = "optional"
                this_jd_id = st.session_state.jd_id.split("//")[0]
                print({'id': str(st.session_state.jd_id)+"_"+str(this_id), 'job_postingid': this_jd_id, 'skill_experienceid':this_id, 'type':type})
                client.table("match_jd_map").upsert({'id': this_jd_id+"_"+str(this_id), 'job_postingid': this_jd_id, 'skill_experienceid':this_id, 'type':type}).execute()
        return result

    # 키워드를 선택하면, 해당 키워드가 포함된 부분을 색상으로 하이라이트하고, 키워드에 해당하는 예상 질문 목록을 조회하는 함수를 호출하고, 결과를 테이블로 표시합니다.:
    for keyword in keywords:
        highlighted_jd = highlighted_jd.replace(keyword, f"<span style='color:#7165E3;font-weight: 900;'>{keyword}</span>")

    container.markdown(highlighted_jd, unsafe_allow_html=True)

    if keywords:    
        # st.session_state.questions = get_questions(keywords)
        get_questions(keywords)
        step3.divider()

        map_col1, map_col2, map_col3 = step3.columns(3)

        # 테이블에서 예상 질문을 선택하면, 필수와 선택으로 구분하여 트리구조로 표시합니
        map_col1.write("검색을 통한 예상 질문입니다. (선택시, 자동 저장)")
        # Create nodes to display
        tree_container = map_col1.container(border=True)

        map_col2.write("검색에 없을 경우, 신규 생성 전에 한번더 확인하세요. (선택시, 자동 저장)")
        all_tree_container = map_col2.container(border=True)

        # 필요하다면 하위 질문을 추가하고, 저장하는 기능을 구현합니다.
        map_col3.write("하위/신규 질문을 추가하려면, 트리구조에서 간선이 1개(1촌 관계)인 상위 keyword를 선택하고, 아래의 입력창에 keyword를 작성하세요.")
        all_new_tree_container = map_col3.container(border=True)
        sub_question = map_col3.text_input("하위 keyword")
        question_type = map_col3.radio("질문의 종류를 선택하세요.", ["not_question//"+"키워드아님.","experience//"+sub_question+" 경험이 있나요?", "tool//"+sub_question+", 업무상 활용 경험이 있나요?", "document//"+sub_question+" 문서 작성 경험이 있나요?", "sector//"+sub_question+" 업계에서의 프로젝트 또는 업무 경험이 있나요?", "startup//"+sub_question+" 스타트업에서 프로젝트 또는 업무 경험이 있나요?"])
        def check_and_condition(checked):
            new_id = []
            for checked_id in [int(item.split("'")[0]) for item in checked if item.split("'")[0]!="0"]:
               this_map = st.session_state.questions["map_dict"][checked_id]
               if this_map["and_condition_list"] and len(this_map["and_condition_list"])>0:
                    new_id = new_id+[str(id) for id in this_map["and_condition_list"]]
            if len(new_id) > 0:
              return list(set(checked + check_and_condition(new_id)))
            else:
              return checked

        with tree_container:
            st.write("예상 질문 목록")
            if "search_tree_refresh" not in st.session_state:
                st.session_state.search_tree_refresh = get_random_string(3)
            if "search_checked" not in st.session_state:
                st.session_state.search_checked = []
            if "search_expanded" not in st.session_state:
                st.session_state.search_expanded = []
            tree_selection = tree_select(st.session_state.tree_data,key=f"search_{st.session_state.search_tree_refresh}",checked=st.session_state.search_checked, expanded=st.session_state.search_expanded)
            
            new_checked = check_same_id(check_and_condition(tree_selection["checked"]))
            st.session_state.search_expanded = tree_selection["expanded"]

            # and로 있는 모든 질문 자동으로 선택.
            if sorted(new_checked)!= sorted(tree_selection["checked"]) and sorted(st.session_state.search_checked) != sorted(new_checked):
                st.session_state.search_checked = new_checked
                st.session_state.search_tree_refresh = get_random_string(3)
                st.rerun()

            if st.button("예상질문 저장"):
               if save_jd_map(tree_selection["checked"]):
                st.session_state.search_checked = []
                new_checked = []
                tree_selection["checked"] = []
                keywords = []
                #st.session_state.keywords = [] => 추가
                tree_container.success("저장 완료")
                time.sleep(1)
                st.session_state.search_tree_refresh = get_random_string(3)
                st.rerun()
            if st.button("초기화",key="reset_search"):
                st.session_state.search_checked = []
                new_checked = []
                tree_selection["checked"] = []
                keywords = []
                st.session_state.search_tree_refresh = get_random_string(3)
                st.rerun()
        with all_tree_container:
            st.write("전체 목록")
            
            if "all_tree_refresh" not in st.session_state:
                st.session_state.all_tree_refresh = get_random_string(3)
            if "all_checked" not in st.session_state:
                st.session_state.all_checked = []
            if "all_expanded" not in st.session_state:
                st.session_state.all_expanded = []
            # f"all_{len(st.session_state.all_checked)}"
            tree_selection = tree_select(st.session_state.all_tree_data,key=f"all_{st.session_state.all_tree_refresh}",checked=st.session_state.all_checked, expanded=st.session_state.all_expanded)
            
            new_checked = check_same_id(check_and_condition(tree_selection["checked"]))
            st.session_state.all_expanded = tree_selection["expanded"]

            # and로 있는 모든 질문 자동으로 선택.
            if sorted(new_checked)!= sorted(tree_selection["checked"]) or sorted(st.session_state.all_checked) != sorted(new_checked):
                st.session_state.all_checked = new_checked
                st.session_state.all_tree_refresh = get_random_string(3)
                st.rerun()

            if st.button("질문 저장"):
                if save_jd_map(tree_selection["checked"]):
                    st.session_state.all_checked = []
                    new_checked = []
                    tree_selection["checked"] = []
                    st.success("저장 완료")
                    st.session_state.all_tree_refresh = get_random_string(3)
                    time.sleep(1)
                    st.rerun()
            if st.button("초기화",key="reset_all"):
                st.session_state.all_checked = []
                new_checked = []
                tree_selection["checked"] = []
                st.session_state.all_tree_refresh = get_random_string(3)
                time.sleep(1)
                st.rerun()
                  
        with all_new_tree_container:
            st.write("전체 목록")
            
            if "new_all_tree_refresh" not in st.session_state:
                st.session_state.new_all_tree_refresh = get_random_string(3)
            if "new_all_expanded" not in st.session_state:
                st.session_state.new_all_expanded = []
            tree_selection = tree_select(st.session_state.new_all_tree_data,key=f"all_new_{st.session_state.new_all_tree_refresh}",expanded=st.session_state.new_all_expanded)
            st.session_state.new_all_expanded = tree_selection["expanded"]
            if map_col3.button("추가하기") and sub_question and question_type and keywords:
                # map 테이블에 하위 질문을 추가하는 쿼리를 작성합니다.
                temp = tree_selection["checked"]
                for item in tree_selection["checked"]:
                   if item.split("'")[0] == "0":
                      temp.remove(item)
                      temp.append(st.session_state.new_tree_zero_dict[item])
                checked = list(set([int(item.split("'")[0]) for item in temp]))
                print(checked)
                input_data = {"keyword": sub_question, "type": question_type.split("//")[0],"search_keyword":[], "parent_skill_experience_list": checked, "and_condition_list": []}
                print(tree_selection["checked"])
                if len(tree_selection["checked"]) > 1:
                   input_data["and_condition_list"] = checked
                query = client.table("match_map").insert(input_data)
                # 쿼리를 실행하고, 결과를 받습니다.
                result = query.execute()
                # 결과가 성공적이면, 트리구조에 하위 질문을 추가합니다.
                print(result.data[0]["skill_experienceid"])
                save_jd_map([str(result.data[0]["skill_experienceid"])])
                map_col3.success("하위 질문이 추가되었습니다.")
                tree_selection["checked"] = []
                # st.session_state.questions = get_questions(keywords)
                st.session_state.new_all_tree_data = []
                st.session_state.new_all_expanded += temp

                get_questions(keywords)
                st.session_state.new_all_tree_refresh = get_random_string(3)
                st.session_state.search_tree_refresh = get_random_string(3)
                st.session_state.all_tree_refresh = get_random_string(3)
                st.rerun()
            else:
                map_col3.error("입력하지 않은 필드가 있습니다.")

step4.write("기능 미구현. 수정 및 삭제는 DB에서만 가능.")

alarmURL.write("[예시]\n821012341234,821012341234,...")
phone_numbers = alarmURL.text_area("위의 예시와 같이 입력해주세요.")
if len(phone_numbers) > 0 and alarmURL.button("등록"):
    with st.spinner('잠시만 기다려 주세요...'):
        progress_text = '잠시만 기다려 주세요...'
        progress_value = 0
        progress_bar = st.progress(progress_value, text=progress_text)
        # 테스트
        admin = sp.create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY, ClientOptions(auto_refresh_token=False, persist_session=False))
        # 배포
        # admin = sp.create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_SERVICE_KEY"], ClientOptions(auto_refresh_token=False, persist_session=False))
        phone_list = phone_numbers.split(",")
        phone_list = [phone.strip().replace("-","").replace("+","") for phone in phone_list]
        user_dict = {} # id와 전화 번호를 저장할 딕셔너리
        need_to_find = []

        for phone in phone_list:
            if len(phone) == 11 and phone[:3] == "010":
                phone = "82" + phone[1:]
            # client.auth.sign_up({"phone": phone,"phone_confirm":True})
            try:
                progress_text = "유저 가입중.."+phone
                result = admin.auth.admin.create_user(
                    {"phone": phone, "phone_confirm":True}
                )
                user_dict[result.user.id] = phone
            except Exception:
                try:
                    progress_text = "유저 조회중.."+phone
                    registed_user = client.table("users").select("id").eq("phone_number",phone).single().execute()
                    user_dict[registed_user.data["id"]] = phone
                except Exception:
                    progress_text = "중복 유저 재확인.."+phone
                    need_to_find.append(phone)
            progress_value += 0.5/len(phone_list)
            progress_bar.progress(progress_value, text=progress_text)

        page = 1
        try_count = 0
        while len(need_to_find) > 0:
            if try_count == 5:
                break
            admin_all_users = admin.auth.admin.list_users(
                page = page,
                per_page=100
            )
            if len(admin_all_users) == 0:
                page = 0
                try_count += 1
            all_users = {user.phone : user.id for user in admin_all_users}
        
            for item in need_to_find:
                if item in all_users.keys():
                    user_dict[all_users[item]] = item
                    need_to_find.remove(item)
            page += 1
            # user_dict[user.data["id"]] = phone # 딕셔너리에 id와 전화 번호 저장
        user_dict_list = []
        for user_key in user_dict.keys():
            # is.gd URL shortener 객체를 생성합니다.
            # shortener = pygdshort.shorten(url)
            s = gdshortener.ISGDShortener()

            # URL을 축약하고 출력합니다.
            short_url = s.shorten("https://jiwon.in10s.co/app?appPath=root&queryKey1=redirect&queryValue1=myNoti&queryKey2=param1&queryValue2="+user_key)
            # print()
            user_dict_list.append({"id":user_key,"phone_number":user_dict[user_key],"url":"https://www.in10s.co?alarmKey="+short_url[0].replace("https://is.gd/","")})
            # print(short_url)

            progress_value += 0.5/len(user_dict.keys())
            progress_text = "URL 생성중.."+short_url[0]
            progress_bar.progress(progress_value, text=progress_text)
        progress_bar.empty()
        df = pd.DataFrame(user_dict_list) # 데이터프레임 생성 ,"email","now_position","work_year","total_work_year"
        st.download_button("csv 파일 다운로드",df.to_csv(index=False),"data.csv","text/csv") # 다운로드 버튼 생성
        st.empty() # text_area 비우기
        if len(need_to_find)>0:
            alarmURL.warning("실패한 번호가 있습니다. 재시도 해주세요\n\n" + ",".join(need_to_find))


print(alarmURL)