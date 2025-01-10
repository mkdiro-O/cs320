import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.preprocessing import PolynomialFeatures

class UserPredictor:
    
    
    def __init__(self):
        self.model = Pipeline([('scaler', StandardScaler()),
                               ('polynomial_features', PolynomialFeatures(degree=2, include_bias=False)),
                               ('classifier', LogisticRegression(class_weight='balanced', penalty='l2', C=1.0, solver='liblinear'))])
    
    def fit(self, train_users, train_logs, train_y):
        train_users = self._add_features(train_users, train_logs)
        X = train_users.drop(columns=['id', 'name'])
        
        X = pd.get_dummies(X, columns=['badge'])
        self.feature_names = X.columns

        train_y = train_y['clicked']
        self.model.fit(X, train_y)
    
    def predict(self, train_users, train_logs):
        train_users = self._add_features(train_users, train_logs)
        X = train_users.drop(columns=['id', 'name'])
        
        X = pd.get_dummies(X, columns=['badge'])
        X = X.reindex(columns=self.feature_names, fill_value=0)

        predictions = self.model.predict(X)
        return predictions
    
    def _add_features(self, train_users, train_logs):
        if 'user_id' in train_logs.columns and 'seconds_spent' in train_logs.columns:
            total_time = train_logs.groupby('user_id')['seconds_spent'].sum().reset_index()
            train_users = pd.merge(train_users, total_time, left_on='id', right_on='user_id', how='left')
            train_users.rename(columns={'seconds_spent': 'total_seconds_spent'}, inplace=True)
        else:
            train_users['total_seconds_spent'] = 0
        return train_users
