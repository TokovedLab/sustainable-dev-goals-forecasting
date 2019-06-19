import pandas as pd

def window_data(data, lag=5,num_windows=3, step=1, predict_year=2010, target=None, impute_func=None):
    """
    Split up input feature dataframe into windowed data.

    Bug: Lags are wrong way around. For example if window width of 5 is specified (lag=5) then the lag=1 column..
        gives the 5th value while lag=5 gives the 1st value in the time window.

    Args:
        data: multiIndex dataframe of feature data with index of (country, year) and columns of the feature names.
        lag: size of window
        num_windows: number of windows to gererate
        step: the delta between the windows. 1 will mean that there is maximum overlap between windows.
        predict_year: the year that we are targetting
        target: feature to be used as target
        impute_func: function that does imputation

    Returns:
        data_regressors
        data_targets
    """

    assert(target in list(data.columns.values)), "Target should be in the input dataframe"

    countries_in_data = list(data.index.levels[0]) 
    idx = pd.IndexSlice

    #Create empty test and training dataframes
    regressors_index = pd.MultiIndex.from_product([countries_in_data,
                                                   list(range(1,num_windows+1)), 
                                                   list(range(1,lag+1))],
                                                  names=[u'country', u'window', u'lag'])

    target_index = pd.MultiIndex.from_product([countries_in_data,
                                               list(range(1,num_windows+1))],
                                              names=[u'country', u'window'])

    data_regressors = pd.DataFrame(index=regressors_index, columns=data.columns)
    data_targets = pd.DataFrame(index=target_index, columns=[target])


    #Each increment of window represents moving back a year in time
    for window in range(num_windows):
        year = predict_year - window

        #Redo Imputation every time we move back a year
        #This maintains the requirement not to use information from future years in our imputations 
        if impute_func is not None:
            data_imp = impute_func(data, upto_year=year-1 )

        data_targets.loc[idx[:,window+1],:] = data_imp.loc[idx[:,str(year)], target].values

        data_regressors.loc[idx[:,window+1,1:lag+1],:] = \
                data_imp.loc[idx[:,str(year-lag):str(year-1)], :].values

    #According to pandas docs on multiIndex usage: For objects to be indexed and sliced effectively, they need to be sorted.
    data_regressors = data_regressors.sort_index()
    data_targets = data_targets.sort_index()

    #unstacking the input features. Each row will now represent a set of features.
    data_regressors  = data_regressors.unstack(level=2)

    return data_regressors, data_targets