"""
Network analysis module for DataScope.

This module provides social network analysis including
hashtag co-occurrence networks and mention networks.
"""

import re
from typing import Dict, List, Tuple, Optional, Any
from collections import Counter, defaultdict
from itertools import combinations

import pandas as pd

from ..utils.logger import get_logger

logger = get_logger(__name__)


class NetworkAnalyzer:
    """
    Analyze social networks from text data.
    
    Builds and analyzes networks based on:
    - Hashtag co-occurrence
    - Mention relationships
    - User interactions
    
    Example:
        >>> analyzer = NetworkAnalyzer()
        >>> network = analyzer.build_hashtag_network(df)
        >>> print(network['top_hashtags'])
    """
    
    def __init__(self, min_edge_weight: int = 2):
        """
        Initialize network analyzer.
        
        Args:
            min_edge_weight: Minimum co-occurrence count for edges
        """
        self.min_edge_weight = min_edge_weight
        self._graph = None
    
    def _extract_hashtags(self, text: str) -> List[str]:
        """Extract hashtags from text."""
        if not text:
            return []
        return [tag.lower() for tag in re.findall(r'#(\w+)', str(text))]
    
    def _extract_mentions(self, text: str) -> List[str]:
        """Extract mentions from text."""
        if not text:
            return []
        return [mention.lower() for mention in re.findall(r'@(\w+)', str(text))]
    
    def build_hashtag_network(self, df: pd.DataFrame, content_column: str = 'content') -> Dict[str, Any]:
        """
        Build a hashtag co-occurrence network.
        
        Args:
            df: DataFrame with content
            content_column: Column containing text
            
        Returns:
            Network data with nodes, edges, and metrics
        """
        logger.info("Building hashtag co-occurrence network")
        
        # Extract hashtags from each post
        all_hashtags = []
        co_occurrences = Counter()
        
        for content in df[content_column].fillna(''):
            hashtags = self._extract_hashtags(content)
            all_hashtags.extend(hashtags)
            
            # Count co-occurrences (pairs in same post)
            if len(hashtags) >= 2:
                for pair in combinations(sorted(set(hashtags)), 2):
                    co_occurrences[pair] += 1
        
        # Count individual hashtags
        hashtag_counts = Counter(all_hashtags)
        
        # Build nodes
        nodes = []
        for tag, count in hashtag_counts.most_common(50):  # Top 50 hashtags
            nodes.append({
                'id': tag,
                'label': f"#{tag}",
                'size': count,
            })
        
        # Build edges (only for top hashtags)
        top_tags = set(h['id'] for h in nodes)
        edges = []
        for (tag1, tag2), weight in co_occurrences.items():
            if weight >= self.min_edge_weight and tag1 in top_tags and tag2 in top_tags:
                edges.append({
                    'source': tag1,
                    'target': tag2,
                    'weight': weight,
                })
        
        # Calculate metrics
        metrics = self._calculate_network_metrics(nodes, edges)
        
        logger.info(f"Network built: {len(nodes)} nodes, {len(edges)} edges")
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metrics': metrics,
            'hashtag_counts': hashtag_counts.most_common(30),
            'type': 'hashtag_cooccurrence',
        }
    
    def build_mention_network(self, df: pd.DataFrame, content_column: str = 'content', author_column: str = 'author') -> Dict[str, Any]:
        """
        Build a mention network (who mentions whom).
        
        Args:
            df: DataFrame with content and author info
            content_column: Column containing text
            author_column: Column containing author username
            
        Returns:
            Network data with nodes, edges, and metrics
        """
        logger.info("Building mention network")
        
        # Extract mentions for each author
        mention_counts = Counter()
        author_activity = Counter()
        edges_dict = defaultdict(int)
        
        for _, row in df.iterrows():
            content = row.get(content_column, '')
            author = row.get(author_column, 'unknown')
            
            mentions = self._extract_mentions(content)
            author_activity[author] += 1
            
            for mention in mentions:
                mention_counts[mention] += 1
                edges_dict[(author, mention)] += 1
        
        # Combine all users
        all_users = set(author_activity.keys()) | set(mention_counts.keys())
        
        # Build nodes (top 50 most active/mentioned)
        user_importance = {}
        for user in all_users:
            user_importance[user] = author_activity.get(user, 0) + mention_counts.get(user, 0)
        
        top_users = sorted(user_importance.items(), key=lambda x: x[1], reverse=True)[:50]
        top_user_set = set(u for u, _ in top_users)
        
        nodes = []
        for user, importance in top_users:
            nodes.append({
                'id': user,
                'label': f"@{user}",
                'size': importance,
                'posts': author_activity.get(user, 0),
                'mentions': mention_counts.get(user, 0),
            })
        
        # Build edges
        edges = []
        for (source, target), weight in edges_dict.items():
            if weight >= self.min_edge_weight and source in top_user_set and target in top_user_set:
                edges.append({
                    'source': source,
                    'target': target,
                    'weight': weight,
                })
        
        # Calculate metrics
        metrics = self._calculate_network_metrics(nodes, edges)
        
        return {
            'nodes': nodes,
            'edges': edges,
            'metrics': metrics,
            'top_mentioned': mention_counts.most_common(20),
            'top_active': author_activity.most_common(20),
            'type': 'mention_network',
        }
    
    def _calculate_network_metrics(self, nodes: List[Dict], edges: List[Dict]) -> Dict[str, Any]:
        """Calculate basic network metrics."""
        if not nodes:
            return {'density': 0, 'avg_degree': 0, 'components': 0}
        
        n = len(nodes)
        e = len(edges)
        
        # Density
        max_edges = n * (n - 1) / 2 if n > 1 else 1
        density = e / max_edges if max_edges > 0 else 0
        
        # Degree distribution
        degree = defaultdict(int)
        for edge in edges:
            degree[edge['source']] += 1
            degree[edge['target']] += 1
        
        avg_degree = sum(degree.values()) / n if n > 0 else 0
        
        # Try using networkx for advanced metrics
        try:
            import networkx as nx
            
            G = nx.Graph()
            for node in nodes:
                G.add_node(node['id'], **node)
            for edge in edges:
                G.add_edge(edge['source'], edge['target'], weight=edge.get('weight', 1))
            
            # Calculate centralities
            if len(G.nodes) > 0:
                betweenness = nx.betweenness_centrality(G)
                closeness = nx.closeness_centrality(G)
                
                # Top central nodes
                top_betweenness = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:5]
                top_closeness = sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:5]
                
                # Connected components
                components = nx.number_connected_components(G)
                
                return {
                    'node_count': n,
                    'edge_count': e,
                    'density': round(density, 4),
                    'avg_degree': round(avg_degree, 2),
                    'components': components,
                    'top_betweenness': top_betweenness,
                    'top_closeness': top_closeness,
                }
        except ImportError:
            logger.warning("networkx not installed, using basic metrics only")
        except Exception as ex:
            logger.warning(f"Advanced metrics failed: {ex}")
        
        return {
            'node_count': n,
            'edge_count': e,
            'density': round(density, 4),
            'avg_degree': round(avg_degree, 2),
        }
    
    def get_network_for_visualization(self, network_data: Dict) -> Dict:
        """
        Prepare network data for visualization (Plotly/D3).
        
        Args:
            network_data: Network data from build methods
            
        Returns:
            Visualization-ready data
        """
        nodes = network_data.get('nodes', [])
        edges = network_data.get('edges', [])
        
        # Create node positions using simple force-directed layout
        # (In practice, you'd use networkx or a JS library)
        import math
        
        n = len(nodes)
        positions = {}
        for i, node in enumerate(nodes):
            angle = 2 * math.pi * i / n
            radius = 1 + (1 - node['size'] / max(n['size'] for n in nodes)) * 0.5
            positions[node['id']] = {
                'x': math.cos(angle) * radius,
                'y': math.sin(angle) * radius,
            }
        
        return {
            'nodes': [
                {
                    **node,
                    'x': positions[node['id']]['x'],
                    'y': positions[node['id']]['y'],
                }
                for node in nodes
            ],
            'edges': edges,
            'metrics': network_data.get('metrics', {}),
        }


def analyze_network(df: pd.DataFrame, network_type: str = 'hashtag', content_column: str = None) -> Dict:
    """
    Convenience function to analyze network from DataFrame.
    
    Args:
        df: DataFrame with text data
        network_type: 'hashtag' or 'mention'
        content_column: Column containing text (auto-detected if None)
        
    Returns:
        Network analysis results
    """
    # Auto-detect content column
    if content_column is None:
        for col in ['cleaned_text', 'content', 'text', 'cleaned_content']:
            if col in df.columns:
                content_column = col
                break
        if content_column is None:
            return {'error': 'No text column found in DataFrame'}
    
    analyzer = NetworkAnalyzer()
    
    if network_type == 'hashtag':
        result = analyzer.build_hashtag_network(df, content_column=content_column)
    elif network_type == 'mention':
        result = analyzer.build_mention_network(df, content_column=content_column)
    else:
        result = {'error': f"Unknown network type: {network_type}"}
    
    return result


def get_network_summary(network_data: Dict) -> str:
    """Generate text summary of network analysis."""
    lines = ["🕸️ Ağ Analizi Özeti", "=" * 40]
    
    metrics = network_data.get('metrics', {})
    lines.append(f"\n📊 Genel Metrikler:")
    lines.append(f"  • Düğüm sayısı: {metrics.get('node_count', 0)}")
    lines.append(f"  • Bağlantı sayısı: {metrics.get('edge_count', 0)}")
    lines.append(f"  • Ağ yoğunluğu: {metrics.get('density', 0):.4f}")
    lines.append(f"  • Ortalama derece: {metrics.get('avg_degree', 0):.2f}")
    
    if 'hashtag_counts' in network_data:
        lines.append(f"\n#️⃣ En Çok Kullanılan Hashtag'ler:")
        for tag, count in network_data['hashtag_counts'][:5]:
            lines.append(f"  • #{tag}: {count}")
    
    if 'top_mentioned' in network_data:
        lines.append(f"\n📣 En Çok Bahsedilenler:")
        for user, count in network_data['top_mentioned'][:5]:
            lines.append(f"  • @{user}: {count}")
    
    return "\n".join(lines)


