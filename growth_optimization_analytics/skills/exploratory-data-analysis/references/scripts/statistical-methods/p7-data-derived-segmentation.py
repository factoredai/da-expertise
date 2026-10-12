"""
P7 — Data-Derived Segmentation Candidates (Dual-Spine Clustering)

For each categorical dimension in the segmentation spine, derive a data-driven
clustering and compare variance explained against the official classification.
Both groupings enter the spine as a dual pair.

This script provides reusable functions. Adapt column names and dimensions
to the specific dataset.
"""

import pandas as pd
import numpy as np
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score


def select_k(X_scaled, k_range=range(2, 9), method='silhouette'):
    """
    Determine optimal cluster count via silhouette analysis.

    Parameters
    ----------
    X_scaled : np.ndarray
        Standardized feature matrix (n_entities, n_features).
    k_range : range
        Candidate values of k to evaluate.
    method : str
        'silhouette' or 'elbow'.

    Returns
    -------
    int : optimal k
    dict : scores for all k values
    """
    scores = {}
    for k in k_range:
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        labels = km.fit_predict(X_scaled)
        if method == 'silhouette':
            scores[k] = silhouette_score(X_scaled, labels)
        else:  # elbow — within-cluster sum of squares
            scores[k] = km.inertia_

    if method == 'silhouette':
        best_k = max(scores, key=scores.get)
    else:
        # Elbow: find the k with largest drop in inertia rate of change
        ks = sorted(scores.keys())
        diffs = [scores[ks[i]] - scores[ks[i+1]] for i in range(len(ks)-1)]
        if len(diffs) > 1:
            second_diffs = [diffs[i] - diffs[i+1] for i in range(len(diffs)-1)]
            best_k = ks[np.argmax(second_diffs) + 1]
        else:
            best_k = ks[0]

    return best_k, scores


def cluster_entities(entity_df, feature_cols, entity_id_col, k=None, k_range=range(2, 9)):
    """
    Cluster entities on standardized features.

    Parameters
    ----------
    entity_df : pd.DataFrame
        One row per entity with feature columns.
    feature_cols : list of str
        Columns to cluster on (2–4 recommended).
    entity_id_col : str
        Column identifying each entity.
    k : int or None
        If None, determined via silhouette analysis.
    k_range : range
        Candidate k values if k is None.

    Returns
    -------
    pd.DataFrame : entity_df with 'cluster_derived' column added
    dict : metadata (k, silhouette_score, centroids)
    """
    X = entity_df[feature_cols].values
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    if k is None:
        k, scores = select_k(X_scaled, k_range)

    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(X_scaled)
    sil = silhouette_score(X_scaled, labels)

    result = entity_df.copy()
    result['cluster_derived'] = labels

    # Centroids in original scale
    centroids = scaler.inverse_transform(km.cluster_centers_)
    centroid_df = pd.DataFrame(centroids, columns=feature_cols)
    centroid_df.index.name = 'cluster'

    return result, {
        'k': k,
        'silhouette': round(sil, 3),
        'centroids': centroid_df,
        'feature_cols': feature_cols,
    }


def compare_groupings(entity_df, metric_col, official_col, derived_col):
    """
    Compare variance explained by official vs data-derived grouping.

    Parameters
    ----------
    entity_df : pd.DataFrame
        Must contain metric_col, official_col, derived_col.
    metric_col : str
        The dependent variable to test against.
    official_col : str
        The official categorical variable.
    derived_col : str
        The data-derived cluster variable.

    Returns
    -------
    dict with eta_squared for each grouping and the gap.
    """
    results = {}
    for label, col in [('official', official_col), ('derived', derived_col)]:
        groups = [grp[metric_col].values
                  for _, grp in entity_df.groupby(col)
                  if len(grp) > 0]
        if len(groups) < 2:
            results[label] = {'eta_sq': 0.0, 'k': 1}
            continue
        H, p = stats.kruskal(*groups)
        k = entity_df[col].nunique()
        n = len(entity_df)
        eta_sq = (H - k + 1) / (n - k) if n > k else 0
        results[label] = {'eta_sq': round(eta_sq, 4), 'k': k, 'H': round(H, 1), 'p': p}

    results['gap'] = round(
        results.get('derived', {}).get('eta_sq', 0) -
        results.get('official', {}).get('eta_sq', 0), 4)

    return results


def name_clusters(entity_df, cluster_col, feature_cols):
    """
    Generate a naming table for clusters based on centroid profiles.

    Returns a DataFrame with one row per cluster showing the distinguishing
    feature (the dimension where that cluster's centroid deviates most from
    the overall mean, in standardized units).

    The analyst should review and replace auto-generated names with
    business-language equivalents before the deliverable.
    """
    overall_means = entity_df[feature_cols].mean()
    overall_stds = entity_df[feature_cols].std()

    rows = []
    for cl in sorted(entity_df[cluster_col].unique()):
        subset = entity_df[entity_df[cluster_col] == cl]
        cl_means = subset[feature_cols].mean()
        # Z-score of cluster centroid vs population
        z_scores = (cl_means - overall_means) / overall_stds.replace(0, 1)
        top_feature = z_scores.abs().idxmax()
        direction = 'high' if z_scores[top_feature] > 0 else 'low'
        rows.append({
            'cluster': cl,
            'n_entities': len(subset),
            'distinguishing_feature': top_feature,
            'direction': direction,
            'z_score': round(z_scores[top_feature], 2),
            'auto_name': f"{direction}-{top_feature} group",
        })

    return pd.DataFrame(rows)
