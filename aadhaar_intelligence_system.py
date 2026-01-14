"""
Aadhaar Stability & Service Load Intelligence System
====================================================
UIDAI Government Analytics Project

Author: Senior Data Scientist
Date: January 14, 2026

This system analyzes Aadhaar enrolment, demographic, and biometric update data
to compute the Aadhaar Stability Index (ASI) and predict future service load.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, r2_score
import warnings
import os
from pathlib import Path

warnings.filterwarnings('ignore')

# Set style for visualizations
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (14, 8)
plt.rcParams['font.size'] = 10


class AadhaarIntelligenceSystem:
    """
    Complete pipeline for Aadhaar data analysis and prediction.
    """
    
    def __init__(self, base_path):
        """
        Initialize the system with base directory path.
        
        Args:
            base_path (str): Base directory containing the three data folders
        """
        self.base_path = Path(base_path)
        self.enrolment_df = None
        self.demographic_df = None
        self.biometric_df = None
        self.master_df = None
        self.predictions_df = None
        
        # Create output directory
        self.output_dir = self.base_path / 'outputs'
        self.output_dir.mkdir(exist_ok=True)
        
        print("=" * 80)
        print("AADHAAR STABILITY & SERVICE LOAD INTELLIGENCE SYSTEM")
        print("=" * 80)
        print(f"Base Path: {self.base_path}")
        print(f"Output Directory: {self.output_dir}")
        print()
    
    
    # =========================================================================
    # SECTION 1: DATA LOADING
    # =========================================================================
    
    def load_all_datasets(self):
        """
        Load all CSV files from the three directories and combine them.
        """
        print("SECTION 1: DATA LOADING")
        print("-" * 80)
        
        # Load enrolment data
        print("Loading Enrolment Data...")
        enrolment_files = list((self.base_path / 'api_data_aadhar_enrolment').glob('*.csv'))
        enrolment_dfs = []
        for file in enrolment_files:
            df = pd.read_csv(file)
            enrolment_dfs.append(df)
            print(f"  ✓ Loaded {file.name}: {len(df):,} records")
        self.enrolment_df = pd.concat(enrolment_dfs, ignore_index=True)
        print(f"  Total Enrolment Records: {len(self.enrolment_df):,}\n")
        
        # Load demographic data
        print("Loading Demographic Update Data...")
        demographic_files = list((self.base_path / 'api_data_aadhar_demographic').glob('*.csv'))
        demographic_dfs = []
        for file in demographic_files:
            df = pd.read_csv(file)
            demographic_dfs.append(df)
            print(f"  ✓ Loaded {file.name}: {len(df):,} records")
        self.demographic_df = pd.concat(demographic_dfs, ignore_index=True)
        print(f"  Total Demographic Records: {len(self.demographic_df):,}\n")
        
        # Load biometric data
        print("Loading Biometric Update Data...")
        biometric_files = list((self.base_path / 'api_data_aadhar_biometric').glob('*.csv'))
        biometric_dfs = []
        for file in biometric_files:
            df = pd.read_csv(file)
            biometric_dfs.append(df)
            print(f"  ✓ Loaded {file.name}: {len(df):,} records")
        self.biometric_df = pd.concat(biometric_dfs, ignore_index=True)
        print(f"  Total Biometric Records: {len(self.biometric_df):,}\n")
        
        print("✓ All datasets loaded successfully!\n")
    
    
    # =========================================================================
    # SECTION 2: DATA CLEANING
    # =========================================================================
    
    def clean_and_standardize(self):
        """
        Clean and standardize all three datasets.
        """
        print("\nSECTION 2: DATA CLEANING & STANDARDIZATION")
        print("-" * 80)
        
        # Clean Enrolment Data
        print("Cleaning Enrolment Data...")
        self.enrolment_df.columns = self.enrolment_df.columns.str.strip().str.lower()
        self.enrolment_df['date'] = pd.to_datetime(self.enrolment_df['date'], format='%d-%m-%Y', errors='coerce')
        self.enrolment_df['state'] = self.enrolment_df['state'].str.strip()
        self.enrolment_df['district'] = self.enrolment_df['district'].str.strip()
        self.enrolment_df['pincode'] = self.enrolment_df['pincode'].astype(str).str.strip()
        
        # Ensure numeric columns
        for col in ['age_0_5', 'age_5_17', 'age_18_greater']:
            self.enrolment_df[col] = pd.to_numeric(self.enrolment_df[col], errors='coerce').fillna(0)
        
        # Remove duplicates
        before = len(self.enrolment_df)
        self.enrolment_df.drop_duplicates(subset=['date', 'state', 'district', 'pincode'], keep='first', inplace=True)
        after = len(self.enrolment_df)
        print(f"  ✓ Removed {before - after:,} duplicate records")
        print(f"  ✓ Final Enrolment Records: {after:,}\n")
        
        # Clean Demographic Data
        print("Cleaning Demographic Update Data...")
        self.demographic_df.columns = self.demographic_df.columns.str.strip().str.lower()
        self.demographic_df['date'] = pd.to_datetime(self.demographic_df['date'], format='%d-%m-%Y', errors='coerce')
        self.demographic_df['state'] = self.demographic_df['state'].str.strip()
        self.demographic_df['district'] = self.demographic_df['district'].str.strip()
        self.demographic_df['pincode'] = self.demographic_df['pincode'].astype(str).str.strip()
        
        # Ensure numeric columns
        for col in ['demo_age_5_17', 'demo_age_17_']:
            self.demographic_df[col] = pd.to_numeric(self.demographic_df[col], errors='coerce').fillna(0)
        
        before = len(self.demographic_df)
        self.demographic_df.drop_duplicates(subset=['date', 'state', 'district', 'pincode'], keep='first', inplace=True)
        after = len(self.demographic_df)
        print(f"  ✓ Removed {before - after:,} duplicate records")
        print(f"  ✓ Final Demographic Records: {after:,}\n")
        
        # Clean Biometric Data
        print("Cleaning Biometric Update Data...")
        self.biometric_df.columns = self.biometric_df.columns.str.strip().str.lower()
        self.biometric_df['date'] = pd.to_datetime(self.biometric_df['date'], format='%d-%m-%Y', errors='coerce')
        self.biometric_df['state'] = self.biometric_df['state'].str.strip()
        self.biometric_df['district'] = self.biometric_df['district'].str.strip()
        self.biometric_df['pincode'] = self.biometric_df['pincode'].astype(str).str.strip()
        
        # Ensure numeric columns
        for col in ['bio_age_5_17', 'bio_age_17_']:
            self.biometric_df[col] = pd.to_numeric(self.biometric_df[col], errors='coerce').fillna(0)
        
        before = len(self.biometric_df)
        self.biometric_df.drop_duplicates(subset=['date', 'state', 'district', 'pincode'], keep='first', inplace=True)
        after = len(self.biometric_df)
        print(f"  ✓ Removed {before - after:,} duplicate records")
        print(f"  ✓ Final Biometric Records: {after:,}\n")
        
        print("✓ All datasets cleaned and standardized!\n")
    
    
    # =========================================================================
    # SECTION 3: DATA MERGING
    # =========================================================================
    
    def merge_datasets(self):
        """
        Merge all three datasets into a master dataset.
        """
        print("\nSECTION 3: DATA MERGING")
        print("-" * 80)
        
        merge_keys = ['date', 'state', 'district', 'pincode']
        
        # Start with enrolment data
        print("Merging datasets using outer joins...")
        self.master_df = self.enrolment_df.copy()
        
        # Merge with demographic data
        self.master_df = self.master_df.merge(
            self.demographic_df,
            on=merge_keys,
            how='outer',
            suffixes=('', '_demo')
        )
        print(f"  ✓ After demographic merge: {len(self.master_df):,} records")
        
        # Merge with biometric data
        self.master_df = self.master_df.merge(
            self.biometric_df,
            on=merge_keys,
            how='outer',
            suffixes=('', '_bio')
        )
        print(f"  ✓ After biometric merge: {len(self.master_df):,} records")
        
        # Fill missing values with 0 for numeric columns
        numeric_cols = self.master_df.select_dtypes(include=[np.number]).columns
        self.master_df[numeric_cols] = self.master_df[numeric_cols].fillna(0)
        
        # Drop rows with missing date
        self.master_df.dropna(subset=['date'], inplace=True)
        
        print(f"  ✓ Final Master Dataset: {len(self.master_df):,} records")
        print(f"  ✓ Columns: {list(self.master_df.columns)}\n")
        
        print("✓ Datasets merged successfully!\n")
    
    
    # =========================================================================
    # SECTION 4: FEATURE ENGINEERING
    # =========================================================================
    
    def engineer_features(self):
        """
        Create meaningful features including the Aadhaar Stability Index (ASI).
        """
        print("\nSECTION 4: FEATURE ENGINEERING")
        print("-" * 80)
        
        # Total enrolments by age group
        self.master_df['total_enrolments'] = (
            self.master_df['age_0_5'] + 
            self.master_df['age_5_17'] + 
            self.master_df['age_18_greater']
        )
        print("  ✓ Created: total_enrolments")
        
        # Total demographic updates
        self.master_df['total_demo_updates'] = (
            self.master_df['demo_age_5_17'] + 
            self.master_df['demo_age_17_']
        )
        print("  ✓ Created: total_demo_updates")
        
        # Total biometric updates
        self.master_df['total_bio_updates'] = (
            self.master_df['bio_age_5_17'] + 
            self.master_df['bio_age_17_']
        )
        print("  ✓ Created: total_bio_updates")
        
        # Total updates (demographic + biometric)
        self.master_df['total_updates'] = (
            self.master_df['total_demo_updates'] + 
            self.master_df['total_bio_updates']
        )
        print("  ✓ Created: total_updates")
        
        # Update ratio
        self.master_df['update_ratio'] = np.where(
            self.master_df['total_enrolments'] > 0,
            self.master_df['total_updates'] / self.master_df['total_enrolments'],
            0
        )
        print("  ✓ Created: update_ratio")
        
        # =====================================================================
        # AADHAAR STABILITY INDEX (ASI)
        # =====================================================================
        # ASI = 1 - (Total Updates / Total Enrolments)
        # High ASI → Stable Aadhaar records
        # Low ASI → Poor data quality, high rework
        
        self.master_df['asi'] = 1 - self.master_df['update_ratio']
        self.master_df['asi'] = self.master_df['asi'].clip(lower=0, upper=1)  # Ensure between 0 and 1
        print("  ✓ Created: asi (Aadhaar Stability Index)")
        
        # Log-transformed features (for better ML performance)
        self.master_df['log_enrolments'] = np.log1p(self.master_df['total_enrolments'])
        self.master_df['log_updates'] = np.log1p(self.master_df['total_updates'])
        print("  ✓ Created: log_enrolments, log_updates")
        
        # Date features
        self.master_df['year'] = self.master_df['date'].dt.year
        self.master_df['month'] = self.master_df['date'].dt.month
        self.master_df['day_of_week'] = self.master_df['date'].dt.dayofweek
        print("  ✓ Created: year, month, day_of_week")
        
        print(f"\n  Total Features: {len(self.master_df.columns)}")
        print("✓ Feature engineering completed!\n")
    
    
    # =========================================================================
    # SECTION 5: EXPLORATORY DATA ANALYSIS (EDA)
    # =========================================================================
    
    def perform_eda(self):
        """
        Generate comprehensive exploratory data analysis and visualizations.
        """
        print("\nSECTION 5: EXPLORATORY DATA ANALYSIS (EDA)")
        print("-" * 80)
        
        # Calculate district-level aggregations
        district_stats = self.master_df.groupby('district').agg({
            'total_enrolments': 'sum',
            'total_bio_updates': 'sum',
            'total_demo_updates': 'sum',
            'asi': 'mean'
        }).reset_index()
        
        district_stats = district_stats.sort_values('total_enrolments', ascending=False).head(20)
        
        # Create comprehensive visualization
        fig = plt.figure(figsize=(20, 12))
        
        # 1. District-wise Enrolment Bar Chart
        ax1 = plt.subplot(2, 3, 1)
        sns.barplot(data=district_stats, x='total_enrolments', y='district', palette='viridis', ax=ax1)
        ax1.set_title('Top 20 Districts by Total Enrolments', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Total Enrolments', fontsize=12)
        ax1.set_ylabel('District', fontsize=12)
        ax1.ticklabel_format(style='plain', axis='x')
        
        # 2. Biometric Updates by District
        ax2 = plt.subplot(2, 3, 2)
        sns.barplot(data=district_stats, x='total_bio_updates', y='district', palette='Reds_r', ax=ax2)
        ax2.set_title('Top 20 Districts by Biometric Updates', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Total Biometric Updates', fontsize=12)
        ax2.set_ylabel('District', fontsize=12)
        ax2.ticklabel_format(style='plain', axis='x')
        
        # 3. Demographic Updates by District
        ax3 = plt.subplot(2, 3, 3)
        sns.barplot(data=district_stats, x='total_demo_updates', y='district', palette='Blues_r', ax=ax3)
        ax3.set_title('Top 20 Districts by Demographic Updates', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Total Demographic Updates', fontsize=12)
        ax3.set_ylabel('District', fontsize=12)
        ax3.ticklabel_format(style='plain', axis='x')
        
        # 4. Date-wise Total Aadhaar Activity
        ax4 = plt.subplot(2, 3, 4)
        date_stats = self.master_df.groupby('date').agg({
            'total_enrolments': 'sum',
            'total_updates': 'sum'
        }).reset_index()
        ax4.plot(date_stats['date'], date_stats['total_enrolments'], label='Enrolments', linewidth=2)
        ax4.plot(date_stats['date'], date_stats['total_updates'], label='Updates', linewidth=2)
        ax4.set_title('Date-wise Aadhaar Activity Trend', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Date', fontsize=12)
        ax4.set_ylabel('Count', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        plt.setp(ax4.xaxis.get_majorticklabels(), rotation=45)
        
        # 5. ASI Comparison Across Districts
        ax5 = plt.subplot(2, 3, 5)
        asi_sorted = district_stats.sort_values('asi', ascending=False).head(20)
        colors = ['green' if x > 0.7 else 'orange' if x > 0.5 else 'red' for x in asi_sorted['asi']]
        sns.barplot(data=asi_sorted, x='asi', y='district', palette=colors, ax=ax5)
        ax5.set_title('Aadhaar Stability Index (ASI) by District', fontsize=14, fontweight='bold')
        ax5.set_xlabel('ASI (Higher = More Stable)', fontsize=12)
        ax5.set_ylabel('District', fontsize=12)
        ax5.axvline(x=0.7, color='green', linestyle='--', alpha=0.5, label='High Stability')
        ax5.axvline(x=0.5, color='orange', linestyle='--', alpha=0.5, label='Medium Stability')
        ax5.legend()
        
        # 6. Update Distribution
        ax6 = plt.subplot(2, 3, 6)
        update_data = pd.DataFrame({
            'Type': ['Demographic', 'Biometric'],
            'Count': [
                self.master_df['total_demo_updates'].sum(),
                self.master_df['total_bio_updates'].sum()
            ]
        })
        ax6.pie(update_data['Count'], labels=update_data['Type'], autopct='%1.1f%%', 
                colors=['#3498db', '#e74c3c'], startangle=90, textprops={'fontsize': 12})
        ax6.set_title('Distribution of Update Types', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        eda_path = self.output_dir / 'eda_comprehensive_analysis.png'
        plt.savefig(eda_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {eda_path}")
        plt.close()
        
        # Additional Analysis: State-level Statistics
        state_stats = self.master_df.groupby('state').agg({
            'total_enrolments': 'sum',
            'total_updates': 'sum',
            'asi': 'mean'
        }).reset_index()
        state_stats = state_stats.sort_values('total_enrolments', ascending=False).head(15)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        x = np.arange(len(state_stats))
        width = 0.35
        
        ax.bar(x - width/2, state_stats['total_enrolments'], width, label='Enrolments', color='#2ecc71')
        ax.bar(x + width/2, state_stats['total_updates'], width, label='Updates', color='#e74c3c')
        
        ax.set_xlabel('State', fontsize=12, fontweight='bold')
        ax.set_ylabel('Count', fontsize=12, fontweight='bold')
        ax.set_title('State-wise Enrolments vs Updates (Top 15 States)', fontsize=14, fontweight='bold')
        ax.set_xticks(x)
        ax.set_xticklabels(state_stats['state'], rotation=45, ha='right')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        state_path = self.output_dir / 'state_wise_analysis.png'
        plt.savefig(state_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {state_path}")
        plt.close()
        
        print("✓ EDA completed and visualizations saved!\n")
    
    
    # =========================================================================
    # SECTION 6: ANOMALY DETECTION
    # =========================================================================
    
    def detect_anomalies(self):
        """
        Identify unstable regions and anomalies in the data.
        """
        print("\nSECTION 6: ANOMALY DETECTION")
        print("-" * 80)
        
        # 1. Districts with Lowest ASI (Most Unstable)
        print("1. Top 10 Districts with LOWEST ASI (Most Unstable):")
        district_asi = self.master_df.groupby('district')['asi'].mean().reset_index()
        district_asi = district_asi.sort_values('asi').head(10)
        print(district_asi.to_string(index=False))
        print()
        
        # 2. PIN Codes with Highest Update Ratio
        print("2. Top 10 PIN Codes with HIGHEST Update Ratio:")
        pincode_ratio = self.master_df.groupby('pincode')['update_ratio'].mean().reset_index()
        pincode_ratio = pincode_ratio.sort_values('update_ratio', ascending=False).head(10)
        print(pincode_ratio.to_string(index=False))
        print()
        
        # 3. Age Groups Causing Most Rework
        print("3. Age Groups Causing Most Updates (Rework Analysis):")
        age_analysis = pd.DataFrame({
            'Age Group': ['5-17', '17+'],
            'Demographic Updates': [
                self.master_df['demo_age_5_17'].sum(),
                self.master_df['demo_age_17_'].sum()
            ],
            'Biometric Updates': [
                self.master_df['bio_age_5_17'].sum(),
                self.master_df['bio_age_17_'].sum()
            ]
        })
        age_analysis['Total Updates'] = age_analysis['Demographic Updates'] + age_analysis['Biometric Updates']
        print(age_analysis.to_string(index=False))
        print()
        
        # 4. States with Highest Instability
        print("4. Top 5 States with LOWEST Average ASI:")
        state_asi = self.master_df.groupby('state')['asi'].mean().reset_index()
        state_asi = state_asi.sort_values('asi').head(5)
        print(state_asi.to_string(index=False))
        print()
        
        # Save anomaly report
        anomaly_report = {
            'Unstable Districts': district_asi,
            'High Update PIN Codes': pincode_ratio,
            'Age Group Analysis': age_analysis,
            'Unstable States': state_asi
        }
        
        with pd.ExcelWriter(self.output_dir / 'anomaly_detection_report.xlsx') as writer:
            for sheet_name, df in anomaly_report.items():
                df.to_excel(writer, sheet_name=sheet_name, index=False)
        
        print(f"  ✓ Saved: {self.output_dir / 'anomaly_detection_report.xlsx'}")
        print("✓ Anomaly detection completed!\n")
        
        return anomaly_report
    
    
    # =========================================================================
    # SECTION 7: MACHINE LEARNING MODEL
    # =========================================================================
    
    def build_ml_model(self):
        """
        Build Random Forest model to predict future biometric update load.
        """
        print("\nSECTION 7: MACHINE LEARNING MODEL")
        print("-" * 80)
        
        print("Target Variable: bio_age_17_ (Biometric updates for age 17+)")
        print("Model: Random Forest Regressor\n")
        
        # Prepare features and target
        # Remove rows where target is 0 to focus on actual update patterns
        ml_df = self.master_df[self.master_df['bio_age_17_'] > 0].copy()
        
        feature_cols = [
            'age_0_5', 'age_5_17', 'age_18_greater',
            'total_enrolments', 'total_demo_updates', 
            'total_updates', 'update_ratio', 'asi',
            'log_enrolments', 'log_updates',
            'month', 'day_of_week'
        ]
        
        X = ml_df[feature_cols].fillna(0)
        y = ml_df['bio_age_17_']
        
        print(f"Training Dataset Size: {len(X):,} records")
        print(f"Features: {len(feature_cols)}")
        print(f"Feature List: {feature_cols}\n")
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )
        
        print(f"Training Set: {len(X_train):,} | Test Set: {len(X_test):,}\n")
        
        # Train model
        print("Training Random Forest Regressor...")
        rf_model = RandomForestRegressor(
            n_estimators=100,
            max_depth=15,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42,
            n_jobs=-1,
            verbose=0
        )
        
        rf_model.fit(X_train, y_train)
        print("  ✓ Model training completed!\n")
        
        # Make predictions
        y_pred_train = rf_model.predict(X_train)
        y_pred_test = rf_model.predict(X_test)
        
        # Evaluate model
        print("MODEL PERFORMANCE:")
        print("-" * 40)
        train_mae = mean_absolute_error(y_train, y_pred_train)
        train_r2 = r2_score(y_train, y_pred_train)
        test_mae = mean_absolute_error(y_test, y_pred_test)
        test_r2 = r2_score(y_test, y_pred_test)
        
        print(f"Training MAE: {train_mae:.2f}")
        print(f"Training R²:  {train_r2:.4f}")
        print(f"Test MAE:     {test_mae:.2f}")
        print(f"Test R²:      {test_r2:.4f}\n")
        
        # Feature importance
        feature_importance = pd.DataFrame({
            'Feature': feature_cols,
            'Importance': rf_model.feature_importances_
        }).sort_values('Importance', ascending=False)
        
        print("FEATURE IMPORTANCE (Top 10):")
        print("-" * 40)
        print(feature_importance.head(10).to_string(index=False))
        print()
        
        # Visualize feature importance
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
        
        # Feature importance plot
        sns.barplot(data=feature_importance.head(10), x='Importance', y='Feature', 
                    palette='viridis', ax=ax1)
        ax1.set_title('Top 10 Feature Importance', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Importance Score', fontsize=12)
        ax1.set_ylabel('Feature', fontsize=12)
        
        # Actual vs Predicted
        sample_size = min(1000, len(y_test))
        sample_indices = np.random.choice(len(y_test), sample_size, replace=False)
        ax2.scatter(y_test.iloc[sample_indices], y_pred_test[sample_indices], 
                    alpha=0.5, s=10, color='#3498db')
        ax2.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 
                 'r--', lw=2, label='Perfect Prediction')
        ax2.set_xlabel('Actual Bio Updates (17+)', fontsize=12)
        ax2.set_ylabel('Predicted Bio Updates (17+)', fontsize=12)
        ax2.set_title(f'Actual vs Predicted (Test Set)\nR² = {test_r2:.4f}, MAE = {test_mae:.2f}', 
                      fontsize=14, fontweight='bold')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        model_path = self.output_dir / 'ml_model_performance.png'
        plt.savefig(model_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {model_path}")
        plt.close()
        
        print("✓ Machine learning model completed!\n")
        
        return rf_model, feature_cols, feature_importance
    
    
    # =========================================================================
    # SECTION 8: PREDICTIONS
    # =========================================================================
    
    def generate_predictions(self, model, feature_cols):
        """
        Generate predictions for the entire dataset.
        """
        print("\nSECTION 8: PREDICTION GENERATION")
        print("-" * 80)
        
        print("Generating predictions for all records...")
        
        # Prepare features
        X_all = self.master_df[feature_cols].fillna(0)
        
        # Generate predictions
        predictions = model.predict(X_all)
        
        # Add to master dataframe
        self.master_df['predicted_bio_load'] = predictions
        self.master_df['predicted_bio_load'] = self.master_df['predicted_bio_load'].clip(lower=0)
        
        print(f"  ✓ Predictions generated for {len(self.master_df):,} records")
        print(f"  ✓ Prediction Statistics:")
        print(f"     - Mean Predicted Load: {predictions.mean():.2f}")
        print(f"     - Median Predicted Load: {np.median(predictions):.2f}")
        print(f"     - Max Predicted Load: {predictions.max():.2f}")
        print(f"     - Min Predicted Load: {predictions.min():.2f}\n")
        
        # Create predictions summary by district
        district_predictions = self.master_df.groupby('district').agg({
            'predicted_bio_load': 'sum',
            'total_enrolments': 'sum',
            'asi': 'mean'
        }).reset_index()
        
        district_predictions = district_predictions.sort_values('predicted_bio_load', ascending=False).head(20)
        
        print("TOP 20 DISTRICTS BY PREDICTED BIOMETRIC LOAD:")
        print("-" * 60)
        print(district_predictions.to_string(index=False))
        print()
        
        # Visualize predictions
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 6))
        
        # Top districts by predicted load
        sns.barplot(data=district_predictions, x='predicted_bio_load', y='district', 
                    palette='Reds_r', ax=ax1)
        ax1.set_title('Top 20 Districts by Predicted Biometric Service Load', 
                      fontsize=14, fontweight='bold')
        ax1.set_xlabel('Predicted Biometric Load', fontsize=12)
        ax1.set_ylabel('District', fontsize=12)
        
        # Correlation: ASI vs Predicted Load
        scatter_data = self.master_df[self.master_df['predicted_bio_load'] > 0].sample(min(5000, len(self.master_df)))
        ax2.scatter(scatter_data['asi'], scatter_data['predicted_bio_load'], 
                    alpha=0.3, s=20, color='#e74c3c')
        ax2.set_xlabel('Aadhaar Stability Index (ASI)', fontsize=12)
        ax2.set_ylabel('Predicted Biometric Load', fontsize=12)
        ax2.set_title('ASI vs Predicted Service Load\n(Lower ASI → Higher Predicted Load)', 
                      fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        pred_path = self.output_dir / 'predictions_analysis.png'
        plt.savefig(pred_path, dpi=300, bbox_inches='tight')
        print(f"  ✓ Saved: {pred_path}")
        plt.close()
        
        print("✓ Prediction generation completed!\n")
        
        return district_predictions
    
    
    # =========================================================================
    # SECTION 9: SAVE OUTPUTS
    # =========================================================================
    
    def save_outputs(self):
        """
        Save all outputs including cleaned data, master dataset, and predictions.
        """
        print("\nSECTION 9: SAVING OUTPUTS")
        print("-" * 80)
        
        # 1. Save cleaned enrolment data
        enrolment_path = self.output_dir / 'cleaned_enrolment_data.csv'
        self.enrolment_df.to_csv(enrolment_path, index=False)
        print(f"  ✓ Saved: {enrolment_path}")
        
        # 2. Save cleaned demographic data
        demographic_path = self.output_dir / 'cleaned_demographic_data.csv'
        self.demographic_df.to_csv(demographic_path, index=False)
        print(f"  ✓ Saved: {demographic_path}")
        
        # 3. Save cleaned biometric data
        biometric_path = self.output_dir / 'cleaned_biometric_data.csv'
        self.biometric_df.to_csv(biometric_path, index=False)
        print(f"  ✓ Saved: {biometric_path}")
        
        # 4. Save master dataset
        master_path = self.output_dir / 'master_dataset_with_asi.csv'
        self.master_df.to_csv(master_path, index=False)
        print(f"  ✓ Saved: {master_path}")
        
        # 5. Save predictions only
        predictions_cols = [
            'date', 'state', 'district', 'pincode',
            'total_enrolments', 'total_updates', 'asi',
            'predicted_bio_load'
        ]
        predictions_df = self.master_df[predictions_cols].copy()
        predictions_path = self.output_dir / 'predictions_biometric_load.csv'
        predictions_df.to_csv(predictions_path, index=False)
        print(f"  ✓ Saved: {predictions_path}")
        
        # 6. Create summary statistics
        summary_stats = {
            'Total Records': len(self.master_df),
            'Total Districts': self.master_df['district'].nunique(),
            'Total States': self.master_df['state'].nunique(),
            'Total PIN Codes': self.master_df['pincode'].nunique(),
            'Date Range': f"{self.master_df['date'].min()} to {self.master_df['date'].max()}",
            'Total Enrolments': self.master_df['total_enrolments'].sum(),
            'Total Updates': self.master_df['total_updates'].sum(),
            'Average ASI': self.master_df['asi'].mean(),
            'Total Predicted Bio Load': self.master_df['predicted_bio_load'].sum()
        }
        
        summary_df = pd.DataFrame(list(summary_stats.items()), columns=['Metric', 'Value'])
        summary_path = self.output_dir / 'summary_statistics.csv'
        summary_df.to_csv(summary_path, index=False)
        print(f"  ✓ Saved: {summary_path}")
        
        print("\n✓ All outputs saved successfully!\n")
    
    
    # =========================================================================
    # MAIN EXECUTION PIPELINE
    # =========================================================================
    
    def run_complete_pipeline(self):
        """
        Execute the complete end-to-end pipeline.
        """
        try:
            # Step 1: Load data
            self.load_all_datasets()
            
            # Step 2: Clean data
            self.clean_and_standardize()
            
            # Step 3: Merge datasets
            self.merge_datasets()
            
            # Step 4: Feature engineering
            self.engineer_features()
            
            # Step 5: EDA
            self.perform_eda()
            
            # Step 6: Anomaly detection
            self.detect_anomalies()
            
            # Step 7: Build ML model
            model, feature_cols, feature_importance = self.build_ml_model()
            
            # Step 8: Generate predictions
            self.generate_predictions(model, feature_cols)
            
            # Step 9: Save outputs
            self.save_outputs()
            
            print("=" * 80)
            print("AADHAAR INTELLIGENCE SYSTEM - PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 80)
            print(f"\n📁 All outputs saved in: {self.output_dir}")
            print("\n✅ DELIVERABLES:")
            print("   1. Cleaned datasets (3 files)")
            print("   2. Master dataset with ASI")
            print("   3. Predictions dataset")
            print("   4. EDA visualizations")
            print("   5. Anomaly detection report")
            print("   6. ML model performance analysis")
            print("   7. Summary statistics")
            print("\n🎯 KEY INSIGHTS:")
            print(f"   • Total Records Analyzed: {len(self.master_df):,}")
            print(f"   • Average ASI: {self.master_df['asi'].mean():.4f}")
            print(f"   • Districts Covered: {self.master_df['district'].nunique()}")
            print(f"   • Predicted Future Bio Load: {self.master_df['predicted_bio_load'].sum():,.0f}")
            print("\n" + "=" * 80 + "\n")
            
        except Exception as e:
            print(f"\n❌ ERROR: {str(e)}")
            import traceback
            traceback.print_exc()


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    # Initialize the system
    base_directory = r"d:\uidai hack"
    
    system = AadhaarIntelligenceSystem(base_directory)
    
    # Run the complete pipeline
    system.run_complete_pipeline()
