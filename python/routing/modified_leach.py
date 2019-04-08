import logging, sys
import config as cf
import numpy as np

from python.network.network import *
from python.network.cluster import *
from python.routing.routing_protocol import *

# Stores the details of the current clusters
# We want to be able to reuse the previous clusters as opposed to LEACH
# which create new clusters on each round
clusters = []
# The number of clusters in the network is determined by the algorithm
# TODO Add Reference
NB_CLUSTERS = 5

class MODIFIED_LEACH(RoutingProtocol):

  def _setup_phase_cluster(self, network, round_nb=None, cluster=None):
    """The clusters members decides which nodes are cluster heads depending on 
    algorithm
    In subsequent rounds, the clusters decides the cluster heads

    TODO: Add Reference to Paper
    """
    logging.info('MODIFIED_LEACH: setup phase by Clusters.')
    # decide which network are cluster heads
    global clusters
    # When clusters themselves selects clusterhead, the reuse their cluster strucuter
    # and pick a new cluster from amongst the cluster members

    logging.info('MODIFIED_LEACH: deciding which nodes are new cluster heads.')
    idx = 0
    for cluster in clusters:
      # If cluster is ineffective i.e no of active nodes is less than
      # 1/4 of original cluster member, base station reshuffle cluster
      if cluster.is_cluster_ineffective():
        self._setup_phase_base_station(network, round_nb)
        break
      cluster.select_new_CH()
  
  def _make_CH(self, node):
    """ Make a node a Cluster Head """
    node.next_hop = cf.BSID
    clusters.append(Cluster(cluster_id, node))

  def _setup_phase_base_station(self, network, round_nb=None):
    """The base station decides which nodes are cluster heads in the first round
    round, depending on a probability. Then it broadcasts this information
    to all network.
    In subsequent rounds, the clusters decides the cluster heads

    TODO: Add Reference to Paper
    """
    # TODO Refactor to remove code redundance
    logging.info('MODIFIED_LEACH: setup phase by base Station.')
    alive_nodes = network.get_alive_nodes()
    # An optimal algorithm for finding number of clusters
    # TODO Add Reference
    global NB_CLUSTERS
    NB_CLUSTERS = np.round(np.sqrt(0.5 * len(alive_nodes) * (cf.THRESHOLD_DIST/np.pi) * \
              (cf.AREA_LENGTH/cf.CLUSTER_BASE_DIST**2)))
    global clusters
    if round_nb == 0 and len(clusters):
      # for first round, all nodes have the same energy levels (HOMOGEANOUS)
      # Cluster heads are determined by distance from the Base Station
      prob_ch = float(NB_CLUSTERS)/float(cf.NB_NODES)
      # Sort nodes by distance form BS
      sort_fn = lambda x: calculate_distance(x, network.base_station)
      sorted_nodes = sorted(alive_nodes, key=sort_fn)
      heads = []
      # When the base station selects clusters, the previous clusters are destroyed
      # and new ones created
      clusters = []
      logging.info('MODIFIED_LEACH: deciding which nodes are cluster heads.')
      idx = 0
      cluster_id = 0
      while len(heads) != NB_CLUSTERS:
        node = sorted_nodes[idx]
        # node will be a cluster head
        self._make_CH(node)
        heads.append(node) # Store Cluster information
        cluster_id += 1
        idx = idx+1 if idx < len(sorted_nodes)-1 else 0
    else:
      # TODO Add Reference
      # Get top two cluster with highest energy and calculate their euclidean distance 
      eligible_CHs = []
      for cluster in clusters:
        eligible_CHs += cluster.top_energy_nodes()[:2]
      sort_fn = lambda x: x.energy_source.energy 
      eligible_CHs.sort(key=sort_fn, reverse=True)
      
    # ordinary network choose nearest cluster heads
    logging.info('MODIFIED_LEACH: ordinary nodes choose nearest nearest cluster head')
    for node in alive_nodes: if node in heads: # node is cluster head continue 
      nearest_head = heads[0]
      cluster = clusters[0]
      # find the nearest cluster head
      for idx, head in enumerate(heads[1:]):
        if calculate_distance(node, nearest_head) > calculate_distance(node, head):
          nearest_head = head
          cluster = clusters[idx+1]
  
      node.next_hop = nearest_head.id
      cluster.add_member(node)

    logging.debug('MODIFIED_LEACH: new clusters--> %s' % clusters)

  def setup_phase(self, network, round_nb=None):
    """ Setup phase varies depending on number of rounds. For the first round the 
    base station selects cluster heads for subsequent rounds, task of cluster head
    selection falls to cluster members
    """
    if round_nb == 0:
      self._setup_phase_base_station(network, round_nb)
    else: 
      self._setup_phase_cluster(network, round_nb)
    network.broadcast_next_hop()
