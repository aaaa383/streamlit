import streamlit as st
import pandas as pd
from ortools.linear_solver import pywraplp


# 各炉の容量
furnace = [1000,500,1500]

# SCIP でソルバーを作成 
solver = pywraplp.Solver.CreateSolver('SCIP')


def create_data_model(df, limit_capacity):
    """サンプルデータの作成
      df: 読み込むDataFrame、num_bins 設定する bin の数、
      limit_item_capacity: bin の中にいれられる item の数の上限
    """
    
    data = {}
    weights = df["Weight"].values.tolist() # 重量
    values = df["Value"].values.tolist() # 評価価値

    data['weights'] = weights
    data['values'] = values

    # 製品リスト
    data['items'] = list(range(len(weights))) 
    # 製品の個数
    data['num_items'] = len(weights)
    # 炉の個数
    data['num_furnace'] = len(limit_capacity)
    # 炉のリスト
    data['furnace'] = list(range(len(limit_capacity)))
    # 炉のキャパシティ
    data['furnace_capacities'] = limit_capacity
    
    return data



# タイトルを表示
st.title('数理最適化サンプルツール')

st.sidebar.markdown("### 1. データの読み込み")
uploaded_file = st.sidebar.file_uploader("CSVファイルをドラッグ&ドロップ、またはブラウザから選択してください", type='csv', key='train')
if uploaded_file is not None:

    #データの読込み
    df = pd.read_csv(uploaded_file)

     #データの表示
    st.sidebar.markdown("### 2. データの情報の表示")
    if st.sidebar.checkbox('データの中身を表示しますか？'):
        st.markdown("### 1. アップロードされたデータを確認します")
        st.dataframe(df)

        data = create_data_model(df, furnace)

        # 変数
        # x[i, j] = 1 if item i is packed in furnace j.
        x = {}
        for i in data['items']:
            for j in data['furnace']:
                x[(i, j)] = solver.IntVar(0, 1, 'x_%i_%i' % (i, j))


        # 制約条件
        # 全てのitemは炉のどこかに1つだけ入る
        for i in data['items']:
            solver.Add(sum(x[i, j] for j in data['furnace']) <= 1)

        # 制約条件
        # furnace_capacitiesで設定した重量以上のitemを格納しない
        for j in data['furnace']:
            solver.Add(
                sum(x[(i, j)] * data['weights'][i]
                    for i in data['items']) <= data['furnace_capacities'][j])
        
        # 目的変数の設定
        objective = solver.Objective()

        for i in data['items']:
            for j in data['furnace']:
                objective.SetCoefficient(x[(i, j)], data['values'][i])
        objective.SetMaximization()

        status = solver.Solve()
    
    # チェック時に上で求めた条件で数理最適化を解く
    st.sidebar.markdown("### 3. 数理最適化の求解")
    if st.sidebar.checkbox('最適化を行いますか？'):
        st.markdown("### 2. 数理最適化の結果を表示")
        ### ナップサック処理結果の取得及び DataFrame 化
        df_knapsack = pd.DataFrame()
        
        if status == pywraplp.Solver.OPTIMAL:
            total_weight = 0
            for j in data['furnace']:
                furnace_weight = 0
                furnace_value = 0
                for i in data['items']:
                    if x[i, j].solution_value() > 0:
                        furnace_weight += data['weights'][i]
                        furnace_value += data['values'][i]

                        # 必要な情報を 一時的な DataFrameに格納して df_knapsack に結合
                        df_tmp = pd.DataFrame(
                            [
                                j, # furnace
                                i, # item
                                data['weights'][i], # weight
                                data['values'][i], # values
                            ]
                        ).T

                        df_tmp.columns=["furnace", "item", "weight", "value"]
                        df_knapsack = pd.concat([df_knapsack, df_tmp], axis=0)
            
                if furnace_weight == 0:
                    break # 何も入らないfurnaceが登場したらbreakで処理を終わらせる
                total_weight += furnace_weight
        else:
            st.exception(Exception('この問題には最適解がありませんでした。'))
        
        st.success('この問題には最適解がありました')
        df_knapsack = df_knapsack.reset_index(drop=True) # indexのリセット

        # テーブルの表示
        st.table(df_knapsack)

    st.sidebar.markdown("### 3. csvダウンロード")
    if st.sidebar.checkbox('csvダウンロード画面を表示しますか？'):
        st.markdown("### 3. 結果のダウンロード")

        st.download_button(
            label='ダウンロードボタン',
            data=df_knapsack.to_csv(index=None).encode('utf-8'),
            file_name='result.csv'
        )
