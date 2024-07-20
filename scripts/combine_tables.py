import pandas as pd

git_df = pd.read_excel('data/Review_Historic_Air_Photos.xlsx', sheet_name=None)
drive_df = pd.read_excel('data/Review_Historic_Air_Photos_Drive.xlsx', sheet_name=None)

if not drive_df.keys() == git_df.keys():
    print('Sheet names do not match.')
else:
    print('Sheet names match, checking individual sheets.')
    # first, check pubs
    print('publications: ')
    diff = git_df['publications'].sort_values('Key', ignore_index=True)\
        .compare(drive_df['publications'].sort_values('Key', ignore_index=True), result_names=('git', 'drive'))

    print(diff)
    if diff.size > 0:
        diff.to_excel('publications_differences.xlsx')

    # then, check geographic, scientific
    for sheet in ['geographic', 'scientific']:
        print(sheet + ': ')
        diff = git_df[sheet].sort_values('Publication Key', ignore_index=True)\
            .compare(drive_df[sheet].sort_values('Publication Key', ignore_index=True), result_names=('git', 'drive'))

        print(diff)
        if diff.size > 0:
            diff.to_excel('{}_differences.xlsx'.format(sheet))

    # then, check datasets, processing, accuracy, outputs
    for sheet in ['datasets', 'processing', 'accuracy', 'outputs']:
        print(sheet + ': ')
        diff = git_df[sheet].sort_values('Key', ignore_index=True)\
            .compare(drive_df[sheet].sort_values('Key', ignore_index=True), result_names=('git', 'drive'))

        print(diff)
        if diff.size > 0:
            diff.to_excel('{}_differences.xlsx'.format(sheet))

