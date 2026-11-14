import pandas as pd
df = pd.read_parquet('data/features/ball_by_ball_with_pressure.parquet')
rinku = df[df['striker_name']=='Rinku Singh']
faced = rinku[rinku['is_ball_faced']]
print('Rinku total faced:', len(faced))
print('Pressure:', faced.is_pressure_delivery.sum(), 'Normal:', (~faced.is_pressure_delivery).sum())
n_norm = (~faced.is_pressure_delivery).sum()
print('Normal SR:', faced[~faced.is_pressure_delivery].runs.sum() / max(1, n_norm) * 100)
print('Pressure SR:', faced[faced.is_pressure_delivery].runs.sum() / max(1, faced.is_pressure_delivery.sum()) * 100)
print('His batting orders:')
print(faced.batting_order.value_counts())
print()
print('Overall pressure pct:', df.is_pressure_delivery.mean()*100)
print('Wicket moderate+:', (df.wicket_pressure.isin(['moderate','high','extreme'])).sum())
print('Recent cluster:', df.recent_wicket_cluster.sum())
print('New batter <5:', (df.batter_balls_faced < 5).sum())
