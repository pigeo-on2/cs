import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import networkx as nx
import os
import numpy as np

def setup_korean_font():
    """한글 폰트 설정
    Returns:
        FontProperties: 설정된 폰트 속성
    Raises:
        RuntimeError: 폰트 파일이 없는 경우
    """
    font_path = os.path.join(os.path.dirname(__file__), 'NanumSquareNeo-cBd.ttf')
    if os.path.exists(font_path):
        font_prop = fm.FontProperties(fname=font_path)
        plt.rcParams['font.family'] = font_prop.get_name()
        plt.rcParams['axes.unicode_minus'] = False
        print(f"폰트 로드 성공: {font_path}")
        return font_prop
    else:
        raise RuntimeError("NanumSquareNeo-cBd.ttf 폰트 파일이 visualizer.py와 같은 폴더에 있어야 합니다.")

def calc_daily_moves(timetable, graph):
    """일별 이동 거리 계산
    Args:
        timetable (dict): 시간표 데이터
        graph (nx.Graph): 그래프 객체
    Returns:
        list: 일별 이동 거리 리스트
    """
    days = ['월요일', '화요일', '수요일', '목요일', '금요일']
    daily_moves = []
    for day in days:
        move = 0
        prev_room = None
        for entry in timetable[day]:
            if entry and prev_room:
                try:
                    path = nx.shortest_path(graph, prev_room, entry['교실'], weight='weight')
                    dist = sum(graph[u][v]['weight'] for u, v in zip(path, path[1:]))
                    move += dist
                except Exception:
                    pass
            if entry:
                prev_room = entry['교실']
        daily_moves.append(move)
    return daily_moves

def plot_timetable(timetable, class_name="", graph=None, save_path=None):
    """시간표 시각화
    Args:
        timetable (dict): 시간표 데이터
        class_name (str): 반 이름
        graph (nx.Graph, optional): 그래프 객체
        save_path (str, optional): 저장할 파일 경로
    """
    fontprop = setup_korean_font()
    days = ['월요일', '화요일', '수요일', '목요일', '금요일']
    periods_per_day = {
        '월요일': 7, '화요일': 7, '수요일': 4, '목요일': 7, '금요일': 5
    }
    max_periods = max(periods_per_day.values())
    table_data = []
    for period in range(max_periods):
        row = []
        for day in days:
            if period < periods_per_day[day]:
                entry = timetable[day][period]
                if entry:
                    row.append(f"{entry['과목']}\n{entry['선생님']}\n{entry['교실']}")
                else:
                    row.append("")
            else:
                row.append("")
        table_data.append(row)
    fig, ax = plt.subplots(figsize=(12, 7))
    ax.axis('off')
    ax.axis('tight')
    table = ax.table(
        cellText=table_data,
        rowLabels=[f"{i+1}교시" for i in range(max_periods)],
        colLabels=days,
        cellLoc='center',
        loc='center'
    )
    # 셀 폰트/크기/간격 조정
    cell_fontsize = 13
    label_fontsize = 14
    title_fontsize = 18
    for key, cell in table.get_celld().items():
        cell.get_text().set_fontsize(cell_fontsize)
        cell.set_height(0.13)
        cell.PAD = 0.15
        if fontprop:
            cell.get_text().set_fontproperties(fontprop)
        if key[0] == 0 or key[1] == -1:  # colLabels or rowLabels
            cell.get_text().set_fontsize(label_fontsize)
            cell.get_text().set_fontweight('bold')
    # 이동량 색상 및 숫자
    if graph is not None:
        daily_moves = calc_daily_moves(timetable, graph)
        max_move = max(daily_moves) if max(daily_moves) > 0 else 1
        for col, move in enumerate(daily_moves):
            color_intensity = move / max_move if max_move > 0 else 0
            for row in range(max_periods):
                cell = table[(row+1, col)]
                cell.set_facecolor((1, 1-color_intensity, 1-color_intensity))
        for col, move in enumerate(daily_moves):
            cell = table.add_cell(max_periods+1, col, width=1/len(days), height=0.08, text=f"{move:.1f}", loc='center', facecolor='lightgray')
            cell.get_text().set_fontsize(label_fontsize)
            cell.get_text().set_fontweight('bold')
            if fontprop:
                cell.get_text().set_fontproperties(fontprop)
    plt.title(f"{class_name}반 시간표", fontproperties=fontprop, fontsize=title_fontsize, fontweight='bold', pad=20)
    plt.tight_layout()
    if save_path:
        if not save_path.lower().endswith('.jpg'):
            save_path = os.path.splitext(save_path)[0] + '.jpg'
        plt.savefig(save_path, bbox_inches='tight', dpi=200, format='jpg')
    plt.show()

def plot_route(graph, path):
    """경로 시각화
    Args:
        graph (nx.Graph): 그래프 객체
        path (list): 경로 노드 리스트
    """
    import matplotlib.pyplot as plt
    import matplotlib.font_manager as fm
    import os
    font_path = os.path.join(os.path.dirname(__file__), 'NanumSquareNeo-cBd.ttf')
    if os.path.exists(font_path):
        fontprop = fm.FontProperties(fname=font_path)
        plt.rcParams['axes.unicode_minus'] = False
    else:
        fontprop = None
    sub_nodes = set(path)
    sub_edges = list(zip(path, path[1:]))
    pos = {n: (graph.nodes[n]['x_coord'], graph.nodes[n]['y_coord']) for n in sub_nodes}
    plt.figure(figsize=(7, 6))
    nx.draw_networkx_nodes(graph, pos, nodelist=sub_nodes, node_color='lightblue')
    nx.draw_networkx_labels(
        graph, pos, labels={n: n for n in sub_nodes},
        font_properties=fontprop,
        font_size=14
    )
    nx.draw_networkx_edges(graph, pos, edgelist=sub_edges, edge_color='red', width=2)
    plt.axis('off')
    plt.tight_layout()
    plt.show() 