import logging
import config as cf
import numpy as np
from python.network.energy_source import *
from python.utils.utils import *

class Cluster(object):
  def __init__(self, id, head=None, members=None):
    self.head = head
    # The first cluster head is also a cluster member
    self.members = [head,]
    if members:
        self.members += members

    self.id = id
  
  def __str__(self):
    return "Cluster %s with %s members" % (self.id, len(self.members))

  def add_member(self, node):
    self.members.append(node)

  def get_alive_members(self):
    """Return nodes that have positive remaining energy and not cluster head"""
    return [node for node in self.members if node.alive and not node.is_head]

  def get_alive_nodes(self):
    """Return nodes that have positive remaining energy."""
    return [node for node in self.members if node.alive]

  def is_cluster_ineffective(self):
    """ Return whether 1/4 of cluster members are inactive and cluster should
    be reshuffled by base station"""
    print('Cluster %s %s %s %s' % (self.id, len(self.members), len(self.get_alive_nodes()), len(self.members) * 0.75))
    return len(self.get_alive_nodes()) < len(self.members) * 0.75

  def _only_active_members(func):
    """This is a decorator. It wraps all energy consuming methods to
    ensure that only active nodes execute this method. It also ensures
    that only active nodes can take part in cluster head shuffling
    """
    def wrapper(self, *args, **kwargs):
      alive_nodes = self.get_alive_members()
      if alive_nodes > 1:
        func(self, alive_nodes, *args, **kwargs)
        return 1
      else:
        return 0
    return wrapper

  @_only_active_members
  def _get_CH(self, active_nodes):
    """ Gets new cluster head based on Modified LEACH algorithm """
    ave_energy = self.get_average_energy()
    nodes_energies =[ node.energy_source.energy for node in active_nodes ]
    # Nodes are eligible for CH iff remaining energy is greater than average 
    # total energy of active nodes
    sort_node_by_energy = lambda x,y: x.energy_source.energy > y.energy_source.energy
    eligible_nodes = sorted([ node for node in active_nodes if \
            node.energy_source.energy >= ave_energy ], sort_node_by_energy)
    print([node.energy for node in eligible_nodes])

    for node in eligible_nodes:
      if node.is_eligible_cluster_head:
        prev_head = self.head
        # Start tracking number of rounds for which previous head is not head
        prev_head.start_round_no_CH_counter()
        self.head = node
        node.next_hop = cf.BSID
        node.reset_round_no_CH_counter()
        prev_head.next_hop = self.head.id
        break
    cluster_members = self.get_alive_members()
    # Update members hop to new head
    for node in cluster_members:
      node.round_pass_no_CH()
      node.next_hop = self.head.id

  def select_new_CH(self):
    self._get_CH()

  @_only_active_members
  def get_average_energy(self, active_nodes):
    """ Get average energy for current active nodes """
    nodes_energies =[ node.energy_source.energy for node in active_nodes ]
    return np.average(nodes_energies)

