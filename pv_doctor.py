import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import matplotlib.dates as mdates
from matplotlib.lines import Line2D

pr_data = r'C:\Users\himan\Downloads\data\data\PR'
ghi_data = r'C:\Users\himan\Downloads\data\data\GHI'

def load_and_concat(folder):
    csv_files = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith('.csv'):
                csv_files.append(os.path.join(root, file))
    print(f"Found {len(csv_files)} CSV files in {folder}")
    dfs = [pd.read_csv(f) for f in csv_files]
    if not dfs:
        print("No CSV files found in", folder)
        return pd.DataFrame()
    return pd.concat(dfs, ignore_index=True)

pr_df = load_and_concat(pr_data)
ghi_df = load_and_concat(ghi_data)

pr_df['Date'] = pd.to_datetime(pr_df['Date'])
ghi_df['Date'] = pd.to_datetime(ghi_df['Date'])

merge_data = pd.merge(pr_df, ghi_df, on='Date', how='inner').sort_values('Date')

merge_data.to_csv('merged_data.csv', index=False)

start_date = input("Enter start date (YYYY-MM-DD) or leave blank for all: ").strip()
end_date = input("Enter end date (YYYY-MM-DD) or leave blank for all: ").strip()


start_date = start_date if start_date else None
end_date = end_date if end_date else None

def plot_pr_evolution(df, pr_col='PR', ghi_col='GHI', date_col='Date', start_date=None, end_date=None):
    df = df.copy()
    df[date_col] = pd.to_datetime(df[date_col])

    if start_date is not None:
        start_date = pd.to_datetime(start_date)
        df = df[df[date_col] >= start_date]
    if end_date is not None:
        end_date = pd.to_datetime(end_date)
        df = df[df[date_col] <= end_date]

    df = df.sort_values(date_col).reset_index(drop=True)

    df['PR_MA30'] = df[pr_col].rolling(window=30, min_periods=1).mean()

    budget_start = 73.9
    budget_decay = 0.008
    years = []
    for d in df[date_col]:
        if d.month >= 7:
            years.append(d.year)
        else:
            years.append(d.year - 1)
    df['Year'] = years
    min_year = df['Year'].min()
    
    df['Budget_PR'] = budget_start * ((1 - budget_decay) ** (df['Year'] - min_year))

    colors = []
    for val in df[ghi_col]:
        if val < 2:
            colors.append('navy')
        elif val < 4:
            colors.append('deepskyblue')
        elif val < 6:
            colors.append('orange')
        else:
            colors.append('brown')
    df['GHI_color'] = colors

    plt.figure(figsize=(16, 8))
    ax = plt.gca()

    ax.scatter(df[date_col], df[pr_col], c=df['GHI_color'], edgecolor='k', s=60, alpha=0.8, label='Daily PR')
    ax.plot(df[date_col], df['PR_MA30'], color='red', linewidth=2, label='30-d Moving Avg (PR)')
    ax.plot(df[date_col], df['Budget_PR'], color='darkgreen', linewidth=2, label='Budget PR')

    above_dates = []
    above_pr = []
    for i in range(len(df)):
        if df[pr_col][i] > df['Budget_PR'][i]:
            above_dates.append(df[date_col][i])
            above_pr.append(df[pr_col][i])
    ax.scatter(above_dates, above_pr, facecolors='none', edgecolors='lime', s=100, linewidths=2, label='Above Budget PR')

    legend_elements = [
        Line2D([0], [0], marker='o', color='w', label='GHI < 2', markerfacecolor='navy', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='2 ≤ GHI < 4', markerfacecolor='deepskyblue', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='4 ≤ GHI < 6', markerfacecolor='orange', markersize=10),
        Line2D([0], [0], marker='o', color='w', label='GHI ≥ 6', markerfacecolor='brown', markersize=10),
        Line2D([0], [0], color='red', lw=2, label='30-d Moving Avg (PR)'),
        Line2D([0], [0], color='darkgreen', lw=2, label='Budget PR'),
        Line2D([0], [0], marker='o', color='lime', label='Above Budget PR', markerfacecolor='none', markersize=10, markeredgewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10)

    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m'))
    plt.xticks(rotation=45)

    ax.set_title('Performance Ratio (PR) Evolution', fontsize=16)
    ax.set_xlabel('Date', fontsize=14)
    ax.set_ylabel('PR', fontsize=14)
    plt.grid(True, alpha=0.3)

    stats_days = [7, 30, 60, 90]
    stats_text = "Avg PR:\n"
    for d in stats_days:
        avg = df[pr_col].tail(d).mean()
        stats_text += f"Last {d}d: {avg:.2f}\n"
    plt.gcf().text(0.82, 0.18, stats_text, fontsize=12, bbox=dict(facecolor='white', alpha=0.7, edgecolor='gray'))

    plt.tight_layout(rect=[0, 0, 0.8, 1])
    plt.show()

    plot_pr_evolution(merge_data, pr_col='PR', ghi_col='GHI', date_col='Date')
