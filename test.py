def classify(row):
    if row['Phi'] and row['Gemma']:
        return 'Both Correct'
    elif row['Phi']:
        return 'Only Phi Correct'
    elif row['Gemma']:
        return 'Only Gemma Correct'
    else:
        return 'Both Wrong'

df['Outcome'] = df.apply(classify, axis=1)
outcome_counts = df.groupby(['Type', 'Outcome']).size().reset_index(name='Count')

# Normalize to get percentage
total_per_type = outcome_counts.groupby('Type')['Count'].transform('sum')
outcome_counts['Percent'] = outcome_counts['Count'] / total_per_type * 100

# Plot
plt.figure(figsize=(10,6))
sns.barplot(data=outcome_counts, x='Type', y='Percent', hue='Outcome')
plt.title('Model Agreement Breakdown per Question Type')
plt.ylabel('Percentage')
plt.show()

