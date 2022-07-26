from matplotlib import pyplot as plt
import os.path
import math as m
import pandas as pd
import numpy as np
from regex import W
from sklearn.cluster import KMeans, SpectralClustering
from sklearn.model_selection import train_test_split
from sklearn.linear_model import Ridge, Lasso
from sklearn.metrics import mean_squared_error
import json


''' 
The following is the starting code for path1 for data reading to make your first step easier.
'dataset_1' is the clean data for path1.
'''
def data():
    pd.set_option('display.max_rows', 10000)
    df = pd.read_csv('NYC_Bicycle_Counts_2016_Corrected.csv')
    df['Brooklyn Bridge']      = pd.to_numeric(df['Brooklyn Bridge'].replace(',','', regex=True))
    df['Manhattan Bridge']     = pd.to_numeric(df['Manhattan Bridge'].replace(',','', regex=True))
    df['Queensboro Bridge']    = pd.to_numeric(df['Queensboro Bridge'].replace(',','', regex=True))
    df['Williamsburg Bridge']  = pd.to_numeric(df['Williamsburg Bridge'].replace(',','', regex=True))
    df['Total'] = pd.to_numeric(df['Total'].replace(',','', regex=True))
    df['Mean Temp'] = (df['High Temp'] + df['Low Temp']) / 2
    df['BB_share'] = df['Brooklyn Bridge'] / df['Total']
    df['MB_share'] = df['Manhattan Bridge'] / df['Total']
    df['QB_share'] = df['Queensboro Bridge'] / df['Total']
    df['WB_share'] = df['Williamsburg Bridge'] / df['Total']



    X_Lt = df['Low Temp'].to_numpy()
    X_Ht = df['High Temp'].to_numpy()
    X_Mt = df['Mean Temp'].to_numpy()
    X_Pr = df['Precipitation'].to_numpy()
    Y_BB = df['Brooklyn Bridge'].to_numpy()
    Y_MB = df['Manhattan Bridge'].to_numpy()
    Y_QB = df['Queensboro Bridge'].to_numpy()
    Y_WB = df['Williamsburg Bridge'].to_numpy()
    return df, X_Lt,X_Ht,X_Mt,X_Pr, Y_BB,Y_MB,Y_QB,Y_WB


def normalize_train(X_train):
    
    X = X_train
    
    mean = np.mean(X, axis=0) #gets the mean
    mean = np.reshape(mean, (mean.shape[0],1)).T
    std = np.std(X, axis=0) #gets the std for each column
    std = np.reshape(std, (std.shape[0],1)).T
    
    #X[:,1:] = (X[:,1:]-mean[:,1:]) / std[:,1:] #to make sure the 1's column isnt normalized
    X = (X-mean) / std

    
    return X, mean, std

def normalize_test(X_test, trn_mean, trn_std):
    X = X_test
    mean = trn_mean
    std = trn_std
    
    #X[:,1:] = (X[:,1:]-mean[:,1:]) / std[:,1:] #to make sure the 1's column isnt normalized
    X = (X-mean) / std
    return X

def rider_prediction(Bridge_coef_data, mean_temp, precipitation):
    l1, l2, pr_coef, mt_coef, mean, std = (Bridge_coef_data['l1'], Bridge_coef_data['l2'], Bridge_coef_data['pr_coef'], Bridge_coef_data['mt_coef'], Bridge_coef_data['trn_mean'], Bridge_coef_data['trn_std'])
    (Nmean_temp, Nprecipitation) = tuple(normalize_test(np.array([[mean_temp, precipitation]]), mean, std).T)
    riders_predicted = l1*pr_coef[1]*(np.exp(pr_coef[0]*Nprecipitation)) + (l2*mt_coef[0]*Nmean_temp)
    
    return riders_predicted[0]
    
def total_rider_prediction(bridge_dictionary, mean_temp, percipitation):
    total = rider_prediction(bridge_dictionary['BB']['coef'], mean_temp, percipitation)
    total += rider_prediction(bridge_dictionary['MB']['coef'], mean_temp, percipitation)
    total += rider_prediction(bridge_dictionary['WB']['coef'], mean_temp, percipitation)
    total += rider_prediction(bridge_dictionary['QB']['coef'], mean_temp, percipitation)

    return total


def bridge_regression(Y_bridge, X_Mt, X_Pr):
    y_brg = Y_bridge
    pr_coef = np.polyfit(X_Pr, np.log(y_brg), 1) #does exponentail regression for the percipitation
    pr_coef[1] = m.exp(pr_coef[1]) #gets the coefficients
    


    X_Mt = np.reshape(X_Mt, (X_Mt.shape[0],1)) #reshape to format for the test split
    X_Pr = np.reshape(X_Pr, (X_Pr.shape[0],1)) #reshape to format for the test split
    Y_bridge = np.reshape(Y_bridge, (Y_bridge.shape[0],1)) #reshape to format for the test split
    [X_train, X_test, y_train, y_test] = train_test_split(X_Mt, Y_bridge, test_size=.3, random_state=0)
    [X_train, trn_mean, trn_std] = normalize_train(X_train)
    X_test = normalize_test(X_test, trn_mean, trn_std)
    lmbda = np.logspace(-3,3,num=10000) #tries to find the line of best fit
    MODEL = []
    MSE = []
    for l in lmbda:
        model = Lasso(alpha=l).fit(X_train, y_train)
        y_predicted = model.predict(X_test)
        mse = mean_squared_error(y_test, y_predicted)
        MODEL.append(model)
        MSE.append(mse)
    
    ind = MSE.index(min(MSE)) #gets the index for the lowest MSE lambda, ie the best fit
    [d_lmbda_best, d_MSE_best, d_model_best] = [lmbda[ind], MSE[ind], MODEL[ind]]
    mt_coef = np.array(d_model_best.coef_).T #is the mean temp coef

    lmbda1 = np.logspace(-1,1,num=2000) #range of weights to combine the two plots
    lmbda2 = np.logspace(-1,1,num=2000) #range of weights to combine the two plots

    MSE_l = []
    X = np.column_stack((X_Mt,X_Pr)) #puts the pr and mt togther
    [X_train, X_test, y_train, y_test] = train_test_split(X, Y_bridge, test_size=.3, random_state=0)
    [X_train, trn_mean, trn_std] = normalize_train(X_train)
    X_test = normalize_test(X_test, trn_mean, trn_std).T
    l1_list = []
    l2_list = []
    for l1 in lmbda1:
        for l2 in lmbda2:
            #computes the predicted values from our coefficients and tries out different weights
            y_expected = (l1*pr_coef[1]*(np.exp(pr_coef[0]*X_test[1]))) + (l2*mt_coef[0]*X_test[0]) 
            
            MSE = mean_squared_error(y_test, y_expected) #gets the MSE
            MSE_l.append(MSE)
            l1_list.append(l1)
            l2_list.append(l2)


    ind = MSE_l.index(min(MSE_l))
    l1 = l1_list[ind]
    l2 = l2_list[ind]
    print(f" l1 = {l1} l2 = {l2} MSE = {MSE_l[ind]}")

    #test = np.array([[75, 1]])
    #print(test.shape)
    #print(trn_mean.shape)
    #print(trn_mean.shape)
    #test = normalize_test(test, trn_mean, trn_std).T
    #print(f"{(l1*pr_coef[1]*(np.exp(pr_coef[0]*test[1]))) + (l2*mt_coef[0]*test[0])}")
    
    #I tried to do a linear plot, but the 0's were thorwing off the regression
    """
    X = np.column_stack((X_Mt,X_Pr))
    [X_train, X_test, y_train, y_test] = train_test_split(X, Y_bridge, test_size=.3, random_state=0)
    [X_train, trn_mean, trn_std] = normalize_train(X_train)
    X_test = normalize_test(X_test, trn_mean, trn_std)
    lmbda = np.logspace(-2,3,num=100)
    MODEL = []
    MSE = []
    for l in lmbda:
        model = Lasso(alpha=l).fit(X_train, y_train)
        y_predicted = model.predict(X_test)
        mse = mean_squared_error(y_test, y_predicted)
        #mse = np.sum(np.power((y_test - y_predicted), 2)) / len(y_brg)
        MODEL.append(model)
        MSE.append(mse)
    
    ind = MSE.index(min(MSE))
    [d_lmbda_best, d_MSE_best, d_model_best] = [lmbda[ind], MSE[ind], MODEL[ind]]
    print(d_MSE_best)
    test = np.array([[75, 1]])
    print(test.shape)
    print(trn_mean.shape)
    test = normalize_test(test, trn_mean, trn_mean)
    coef = np.array(d_model_best.coef_).T
    print(np.matmul(test,coef))
    """
    #I tried to do a multivariate polynomial regression but the 
    """
    # best_degree = 0
    # score_list = []
    # model_list = []
    # deg_list = []
    # trn_mean_list = []
    # trn_std_list = []
    # #try linear plot
    # best_MSE, best_degree, best_lambda, best_model, best_mean, best_std= (1000000000000000,0,0,0,0,0)
    # for deg in range(1,10):
        
    #     poly = PolynomialFeatures(degree=deg)
    #     X_poly = poly.fit_transform(X)
    #     [X_train, X_test, y_train, y_test] = train_test_split(X_poly, Y_bridge, test_size=.25, random_state=0)
    #     [X_train, trn_mean, trn_std] = normalize_train(X_train)
    #     trn_mean_list.append(trn_mean)
    #     trn_std_list.append(trn_std)

    #     X_test = normalize_test(X_test, trn_mean, trn_std)
        
    #     # regression = linear_model.LinearRegression()
    #     # model = regression.fit(X_train, y_train)
    #     # score = model.score(X_test, y_test)
    #     # score_list.append(abs(score))
    #     # model_list.append(model)
    #     # deg_list.append(deg)
        
    #     lmbda = np.logspace(-2,3,num=100)
    #     MODEL = []
    #     MSE = []
    #     for l in lmbda:
    #         model = Ridge(alpha=l).fit(X_train, y_train)
    #         y_predicted = model.predict(X_test)
    #         mse = mean_squared_error(y_test, y_predicted)
    #         MODEL.append(model)
    #         MSE.append(mse)
        
    #     ind = MSE.index(min(MSE))
    #     [d_lmbda_best, d_MSE_best, d_model_best] = [lmbda[ind], MSE[ind], MODEL[ind]]
        
    #     # print(d_MSE_best)
    #     # print(d_lmbda_best)
    #     # print(deg)

    #     if(d_MSE_best < best_MSE):
    #         best_MSE = d_MSE_best
    #         best_degree = deg
    #         best_lambda = d_lmbda_best
    #         best_model = d_model_best
    #         best_mean = trn_mean
    #         best_std = trn_std
    
    # print(best_MSE)
    # print(best_degree)
    # print(best_model.coef_)

    # # ind = score_list.index(min(score_list))
    # # best_degree = deg_list[ind]
    # # coef = model_list[ind].coef_.T
    # poly = PolynomialFeatures(degree=best_degree)
    # test = np.array([[80, 0]])
    # test = poly.fit_transform(test)
    # test = normalize_test(test, best_mean, best_std)
    
    # # X_poly = poly.fit_transform(test)
    # # X_poly = normalize_test(X_poly, trn_mean_list[ind], trn_std_list[ind])
    # # print(X_poly[:].shape)
    # print(test.shape)
    # coef = np.array(best_model.coef_).T
    # print(coef.shape)
    # print(np.matmul(test[:,:],coef[:,:]))
    """
    return l1, l2, pr_coef, mt_coef, trn_mean, trn_std

def rain_temp_cluster(df, num_clusters=5):
    total = df[['Precipitation','Mean Temp']].values
    std = np.std(total, axis=0)
    mean = np.mean(total, axis=0)
    total = (total - mean) / std
    SSE_list = []
    for i in range(1,11):
        k_means = KMeans(n_clusters=i,init='k-means++', random_state=0)
        k_means.fit(total)
        SSE_list.append(k_means.inertia_)
    
    # plt.plot(np.arange(1,11),SSE_list)
    # plt.xlabel('Clusters')
    # plt.ylabel('SSE')
    # plt.title("Number of Clusters vs SSE Value")
    # plt.show() #the ideal cluster is 3 or 5

    k_means = KMeans(n_clusters=num_clusters,init='k-means++', random_state=0)
    k_means.fit(total)
    cluster_data = k_means.labels_ #append on to the you data
    cluster_locations = k_means.cluster_centers_
    df['weather_cluster'] = cluster_data.tolist() #adds the clustered data to the list
    
    #reorders the data, to make it visually easier
    df = df[["Date","Day","High Temp","Low Temp","Mean Temp","Precipitation","weather_cluster","Brooklyn Bridge","Manhattan Bridge","Williamsburg Bridge","Queensboro Bridge","Total","BB_share","MB_share","QB_share","WB_share"]]
    return df, cluster_locations

def weather_bridge_precentage(df_clusterd, bridge_dict):

    rider_change_list = [[0,0,0,0]]
    #gets the ridership change
    for i in range(df_clusterd.shape[0]-1):
        ridership_change = df_clusterd.loc[i+1,['Brooklyn Bridge','Manhattan Bridge','Williamsburg Bridge','Queensboro Bridge']] / df_clusterd.loc[i,['Brooklyn Bridge','Manhattan Bridge','Williamsburg Bridge','Queensboro Bridge']]
        rider_change_list.append(ridership_change.tolist())
    precent_change_df = pd.DataFrame(rider_change_list)
    #add the changes to the df
    df_clusterd.loc[:,'BB_percent_change'] = precent_change_df[0]
    df_clusterd.loc[:,'MB_percent_change'] = precent_change_df[1]
    df_clusterd.loc[:,'WB_percent_change'] = precent_change_df[2]
    df_clusterd.loc[:,'QB_percent_change'] = precent_change_df[3]
    
    # avrg_precent_change_list = (precent_change_df.sum(axis=0) / precent_change_df.shape[0])
    # print(avrg_precent_change_list)


    bridge_dataDF = df_clusterd[['Brooklyn Bridge','Manhattan Bridge','Williamsburg Bridge','Queensboro Bridge','weather_cluster']]
    total_riders = bridge_dataDF.sum(axis=0).tolist() #gets the total riders for each bridge

    


    cluster_df = []
    for i in range(df_clusterd.nunique()['weather_cluster']): #get total ridership for each cluster for each bridge
        cluster_list = bridge_dataDF[bridge_dataDF['weather_cluster'] == i].sum(axis=0).tolist()[:-1]
        cluster_df.append(cluster_list)
    cluster_df = pd.DataFrame(cluster_df)#create df from the cluster info list
    

    for i in range(4): #gets cluster percentage
        cluster_df[f"{i}p"] = cluster_df[i] / total_riders[i]
    
    
    #stores the data from all the bridges in a dictionary, where each bridge intitals is key to both their plot coefs & bridge statistics
    bridge_complete_dictionary = {'BB': {"coef":bridge_dict['BB'], "stats":{'total_riders':total_riders[0], 'cluster_rider_amnt':cluster_df[0].tolist(), 'cluster_rider_percentage':cluster_df['0p'].to_list()}}}
    bridge_complete_dictionary['MB'] = {"coef":bridge_dict['MB'], "stats":{'total_riders':total_riders[1], 'cluster_rider_amnt':cluster_df[1].tolist(), 'cluster_rider_percentage':cluster_df['1p'].to_list()}}
    bridge_complete_dictionary['WB'] = {"coef":bridge_dict['WB'], "stats":{'total_riders':total_riders[2], 'cluster_rider_amnt':cluster_df[2].tolist(), 'cluster_rider_percentage':cluster_df['2p'].to_list()}}
    bridge_complete_dictionary['QB'] = {"coef":bridge_dict['QB'], "stats":{'total_riders':total_riders[3], 'cluster_rider_amnt':cluster_df[3].tolist(), 'cluster_rider_percentage':cluster_df['3p'].to_list()}}
    bridge_complete_dictionary['Documentation'] = {'coef':{'l1':'The weight of the inverse exponential for percipitation', 'l2':'The weight of the linear plot for mean temp', 'pr_coef':'pr_coef[0] the coeficient for the exponent, pr_coef[1] the coef for the mutltiper', 'mt_coef':'coef for the mean temp plot'}, 'stats':{'total':'total riders on the bridge for the total data set', 'cluster_rider_amnt':'the total amnt of riders for each cluster (list value 0 stores the amnt for the cluster 0)', 'cluster_rider_percentage':'the precentage of total riders for the bridge which rode in set cluster conditions'}}
    return df_clusterd, bridge_complete_dictionary

def day_of_week(df, num_bicyclists):
    
    #finding average for each day, adds new column with only data from each day of the week
    df['Fridays'], df['Saturdays'], df['Sundays'], df['Mondays'], df['Tuesdays'], df['Wednesdays'], df['Thursdays'] = pd.DataFrame(df['Total'][0::7]), pd.DataFrame(df['Total'][1::7]), pd.DataFrame(df['Total'][2::7]), pd.DataFrame(df['Total'][3::7]), pd.DataFrame(df['Total'][4::7]), pd.DataFrame(df['Total'][5::7]), pd.DataFrame(df['Total'][6::7])
    friday_data, saturday_data, sunday_data, monday_data, tuesday_data, wednesday_data, thursday_data = (df['Fridays'], df['Saturdays'], df['Sundays'], df['Mondays'], df['Tuesdays'], df['Wednesdays'], df['Thursdays'])
    friday_avg, saturday_avg, sunday_avg, monday_avg, tuesday_avg, wednesday_avg, thursday_avg = (int(friday_data.mean()), int(saturday_data.mean()), int(sunday_data.mean()), int(monday_data.mean()), int(tuesday_data.mean()), int(wednesday_data.mean()), int(thursday_data.mean()))
    
    daily_avg_dictionary = {friday_avg:'Friday', saturday_avg:'Saturday', sunday_avg:'Sunday', monday_avg:'Monday', tuesday_avg:'Tuesday', wednesday_avg:'Wednesday', thursday_avg:'Thursday'} #dictionary to map each average value to outputtable string
    traffic = lambda input_traffic: daily_avg_dictionary.get(min(daily_avg_dictionary, key = lambda x: abs(x - input_traffic))) #finds which value is the least distance from the input value
    return traffic(num_bicyclists)

def ranking_func(df, bridge_dictionary):
    #print(df.shape)
    BB_day_score = []
    MB_day_score = []
    WB_day_score = []
    QB_day_score = []

    for i in range(df.shape[0]):
        cluster_value = df.loc[i,['weather_cluster']].tolist()[0]
        BBmarket_share,MBmarket_share,WBmarket_share,QBmarket_share = df.loc[i, ['BB_share','MB_share','WB_share','QB_share']].tolist()
        BBcluster_prcnt, MBcluster_prcnt, WBcluster_prcnt, QBcluster_prcnt = [bridge_dictionary['BB']['stats']['cluster_rider_percentage'][cluster_value], bridge_dictionary['MB']['stats']['cluster_rider_percentage'][cluster_value], bridge_dictionary['WB']['stats']['cluster_rider_percentage'][cluster_value], bridge_dictionary['QB']['stats']['cluster_rider_percentage'][cluster_value]]
        BB_day_score.append(BBmarket_share*BBcluster_prcnt)
        MB_day_score.append(MBmarket_share*MBcluster_prcnt)
        WB_day_score.append(WBmarket_share*WBcluster_prcnt)
        QB_day_score.append(QBmarket_share*QBcluster_prcnt)
    
    total_sum_scores_dict = {'BB':sum(BB_day_score), 'MB':sum(MB_day_score), 'WB':sum(WB_day_score), 'QB':sum(QB_day_score)}
    bridge_scores_ranked = {}
    for i in range(4):#find the max values from unsorted list
        max_value = max(total_sum_scores_dict, key=total_sum_scores_dict.get)
        bridge_scores_ranked[max_value] = total_sum_scores_dict[max_value]
        del total_sum_scores_dict[max_value]
    
    bridge_ranked_stats_list = []
    for i in range(4):#extracts the indo from the dictionary
        bridge_rank_info = [i+1, list(bridge_scores_ranked.keys())[i], list(bridge_scores_ranked.values())[i]]
        bridge_ranked_stats_list.append(bridge_rank_info)
    
    return bridge_ranked_stats_list

def main():
    [df, X_Lt,X_Ht,X_Mt,X_Pr, Y_BB,Y_MB,Y_QB,Y_WB] = data()
    
    #bassically saves computing time, and sees if the time consuming bridge prediction is already written 
    #if not it computes it and saves it to a json, to save time 

    if (os.path.exists("bridge_weather_coef.json")):
        with open("bridge_weather_coef.json") as file:
            bridge_dictionary = json.loads(file.read())
    else:
        #takes about 10~20 mintues to finish the computations
        [l1, l2, Pr_coef, Mt_coef, trn_mean, trn_std] = bridge_regression(Y_BB, X_Mt, X_Pr)
        bridge_dictionary = {"BB":{"l1":l1, "l2":l2, "pr_coef":Pr_coef.tolist(), "mt_coef":Mt_coef.tolist(), "trn_mean": trn_mean.tolist(), "trn_std":trn_std.tolist()}}
        [l1, l2, Pr_coef, Mt_coef, trn_mean, trn_std] = bridge_regression(Y_MB, X_Mt, X_Pr)
        bridge_dictionary['MB'] = {"l1":l1, "l2":l2, "pr_coef":Pr_coef.tolist(), "mt_coef":Mt_coef.tolist(), "trn_mean": trn_mean.tolist(), "trn_std":trn_std.tolist()}
        [l1, l2, Pr_coef, Mt_coef, trn_mean, trn_std] = bridge_regression(Y_QB, X_Mt, X_Pr)
        bridge_dictionary['QB'] = {"l1":l1, "l2":l2, "pr_coef":Pr_coef.tolist(), "mt_coef":Mt_coef.tolist(), "trn_mean": trn_mean.tolist(), "trn_std":trn_std.tolist()}
        [l1, l2, Pr_coef, Mt_coef, trn_mean, trn_std] = bridge_regression(Y_WB, X_Mt, X_Pr)
        bridge_dictionary['WB'] = {"l1":l1, "l2":l2, "pr_coef":Pr_coef.tolist(), "mt_coef":Mt_coef.tolist(), "trn_mean": trn_mean.tolist(), "trn_std":trn_std.tolist()}
        
        with open("bridge_weather_coef.json", "w") as file:
            file.write(json.dumps(bridge_dictionary))

    
    
    df_clusterd, cluster_centers = rain_temp_cluster(df, 5) #gets the weather clusters and the cluster centers, ideally either 3 or 5
    df, bridge_dictionary = weather_bridge_precentage(df_clusterd, bridge_dictionary) #gets the bridge statistics to append to the dictionary
    bridge_ranking_list = ranking_func(df, bridge_dictionary)
    
    #print(df)
    #print(bridge_dictionary['Documentation'])

    #cluster_rider_prcnt * market_share == weight for each bridge
    #sum up the weight and dived by the number of number of dataset
    
    #print("Today is: ", day_of_week(df, 14000)) #returns predicted day of the week based on number of riders in a given day, 14000 as an example

if __name__ == "__main__":
    main()
