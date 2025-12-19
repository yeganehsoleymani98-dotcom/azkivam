import kagglehub

# Download latest version
path = kagglehub.dataset_download("bekkarmerwan/retail-sales-dataset-sample-transactions")

print("Path to dataset files:", path)

# حذف ردیف‌هایی که CustomerID ندارند
df = df.dropna(subset=['CustomerID'])

# تاریخ رو به datetime تبدیل می‌کنیم
df['InvoiceDate'] = pd.to_datetime(df['InvoiceDate'])

df.info()

# برای Recency از آخرین تاریخ موجود در داده + 1 روز استفاده می‌کنیم
NOW = df['InvoiceDate'].max() + dt.timedelta(days=1)

rfm = df.groupby('CustomerID').agg({
    'InvoiceDate': lambda x: (NOW - x.max()).days,
    'InvoiceNo': 'nunique',
    'TotalPrice': lambda x: (x).sum()
})

rfm.rename(columns={
    'InvoiceDate': 'Recency',
    'InvoiceNo': 'Frequency',
    'TotalPrice': 'Monetary'
}, inplace=True)

rfm.head()


rfm['R_Score'] = pd.qcut(rfm['Recency'], 5, labels=range(5, 0, -1))
rfm['F_Score'] = pd.qcut(rfm['Frequency'], 5, labels=range(1, 6))
rfm['M_Score'] = pd.qcut(rfm['Monetary'], 5, labels=range(1, 6))

rfm['RFM_Segment'] = rfm['R_Score'].astype(str) + rfm['F_Score'].astype(str) + rfm['M_Score'].astype(str)
rfm['RFM_Score'] = rfm[['R_Score','F_Score','M_Score']].sum(axis=1)

rfm.head()

# مشتریان با بالاترین RFM
top_customers = rfm[rfm['RFM_Score'] >= 13].sort_values('RFM_Score', ascending=False)
top_customers.head()

###