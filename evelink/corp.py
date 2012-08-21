from evelink import api, constants
from evelink.parsing.assets import parse_assets
from evelink.parsing.contact_list import parse_contact_list
from evelink.parsing.contract_items import parse_contract_items
from evelink.parsing.contracts import parse_contracts
from evelink.parsing.industry_jobs import parse_industry_jobs
from evelink.parsing.kills import parse_kills
from evelink.parsing.orders import parse_market_orders
from evelink.parsing.wallet_journal import parse_wallet_journal
from evelink.parsing.wallet_transactions import parse_wallet_transactions

class Corp(object):
    """Wrapper around /corp/ of the EVE API.

    Note that a valid corp API key is required.
    """

    def __init__(self, api):
        self.api = api

    def industry_jobs(self):
        """Get a list of jobs for a corporation."""

        api_result = self.api.get('corp/IndustryJobs')

        return parse_industry_jobs(api_result)

    def npc_standings(self):
        """Returns information about the corporation's standings towards NPCs.

        NOTE: This is *only* NPC standings. Player standings are accessed
        via the 'contacts' method.
        """
        api_result = self.api.get('corp/Standings')
        container = api_result.find('corporationNPCStandings')

        rowsets = dict((r.attrib['name'], r) for r in container.findall('rowset'))
        results = {
            'agents': {},
            'corps': {},
            'factions': {},
        }

        _standing_types = {
            'agents': 'agents',
            'corps': 'NPCCorporations',
            'factions': 'factions',
        }

        for key, rowset_name in _standing_types.iteritems():
            for row in rowsets[rowset_name].findall('row'):
                a = row.attrib
                standing = {
                    'id': int(a['fromID']),
                    'name': a['fromName'],
                    'standing': float(a['standing']),
                }
                results[key][standing['id']] = standing

        return results

    def kills(self, before_kill=None):
        """Look up recent kills for a corporation.

        before_kill:
            Optional. Only show kills before this kill id. (Used for paging.)
        """

        params = {}
        if before_kill is not None:
            params['beforeKillID'] = before_kill
        api_result = self.api.get('corp/KillLog', params)

        return parse_kills(api_result)

    def wallet_info(self):
        """Get information about corp wallets."""

        api_result = self.api.get('corp/AccountBalance')

        rowset = api_result.find('rowset')
        results = {}
        for row in rowset.findall('row'):
            wallet = {
                'balance': float(row.attrib['balance']),
                'id': int(row.attrib['accountID']),
                'key': int(row.attrib['accountKey']),
            }
            results[wallet['key']] = wallet

        return results

    def wallet_journal(self, before_id=None, limit=None):
        """Returns wallet journal for a corporation."""

        params = {}
        if before_id is not None:
            params['fromID'] = before_id
        if limit is not None:
            params['rowCount'] = limit
        api_result = self.api.get('corp/WalletJournal', params)

        return parse_wallet_journal(api_result)

    def wallet_transactions(self, before_id=None, limit=None):
        """Returns wallet transactions for a corporation."""

        params = {}
        if before_id is not None:
            params['fromID'] = before_id
        if limit is not None:
            params['rowCount'] = limit
        api_result = self.api.get('corp/WalletTransactions', params)

        return parse_wallet_transactions(api_result)

    def orders(self):
        """Return a corporation's buy and sell orders."""
        api_result = self.api.get('corp/MarketOrders')

        return parse_market_orders(api_result)

    def assets(self):
        """Get information about corp assets.

        Each item is a dict, with keys 'id', 'item_type_id',
        'quantity', 'location_id', 'location_flag', and 'packaged'.
        'location_flag' denotes additional information about the
        item's location; see
        http://wiki.eve-id.net/API_Inventory_Flags for more details.

        If the item corresponds to a container, it will have a key
        'contents', which is itself a list of items in the same format
        (potentially recursively holding containers of its own).  If
        the contents do not have 'location_id's of their own, they
        inherit the 'location_id' of their parent container, for
        convenience.

        At the top level, the result is a dict mapping location ID
        (typically a solar system) to a dict containing a 'contents'
        key, which maps to a list of items.  That is, you can think of
        the top-level values as "containers" with no fields except for
        "contents" and "location_id".
        """
        api_result = self.api.get('corp/AssetList')
        return parse_assets(api_result)

    def faction_warfare_stats(self):
        """Returns stats from faction warfare if this corp is enrolled.

        NOTE: This will raise an APIError if the corp is not enrolled in
        Faction Warfare.
        """
        api_result = self.api.get('corp/FacWarStats')

        _str, _int, _float, _bool, _ts = api.elem_getters(api_result)

        return {
            'faction': {
                'id': _int('factionID'),
                'name': _str('factionName'),
            },
            'start_ts': _ts('enlisted'),
            'pilots': _int('pilots'),
            'kills': {
                'yesterday': _int('killsYesterday'),
                'week': _int('killsLastWeek'),
                'total': _int('killsTotal'),
            },
            'points': {
                'yesterday': _int('victoryPointsYesterday'),
                'week': _int('victoryPointsLastWeek'),
                'total': _int('victoryPointsTotal'),
            },
        }

    def contract_items(self, contract_id):
        """Lists items that a specified contract contains"""
        api_result = self.api.get('corp/ContractItems',
            {'contractID': contract_id})

        return parse_contract_items(api_result)

    def contracts(self):
        """Get information about corp contracts."""
        api_result = self.api.get('corp/Contracts')
        return parse_contracts(api_result)

    def shareholders(self):
        """Get information about a corp's shareholders."""
        api_result = self.api.get('corp/Shareholders')

        results = {
            'char': {},
            'corp': {},
        }
        rowsets = dict((r.attrib['name'], r) for r in api_result.findall('rowset'))

        for row in rowsets['characters'].findall('row'):
            a = row.attrib
            holder = {
                'id': int(a['shareholderID']),
                'name': a['shareholderName'],
                'corp': {
                    'id': int(a['shareholderCorporationID']),
                    'name': a['shareholderCorporationName'],
                },
                'shares': int(a['shares']),
            }
            results['char'][holder['id']] = holder

        for row in rowsets['corporations'].findall('row'):
            a = row.attrib
            holder = {
                'id': int(a['shareholderID']),
                'name': a['shareholderName'],
                'shares': int(a['shares']),
            }
            results['corp'][holder['id']] = holder

        return results

    def contacts(self):
        """Return the corp's corp and alliance contact lists."""
        api_result = self.api.get('corp/ContactList')
        return parse_contact_list(api_result)

    def titles(self):
        """Returns information about the corporation's titles."""
        api_result = self.api.get('corp/Titles')

        rowset = api_result.find('rowset')
        results = {}
        for row in rowset.findall('row'):
            a = row.attrib
            title = {
                'id': int(a['titleID']),
                'name': a['titleName'],
                'roles': {},
                'can_grant': {},
            }
            rowsets = dict((r.attrib['name'], r) for r in row.findall('rowset'))

            def get_roles(rowset_name):
                roles = {}
                for role_row in rowsets[rowset_name].findall('row'):
                    ra = role_row.attrib
                    role = {
                        'id': int(ra['roleID']),
                        'name': ra['roleName'],
                        'description': ra['roleDescription'],
                    }
                    roles[role['id']] = role
                return roles

            for key, rowset_name in constants.Corp.role_types.iteritems():
                roles = get_roles(rowset_name)
                title['roles'][key] = roles

            for key, rowset_name in constants.Corp.grantable_types.iteritems():
                roles = get_roles(rowset_name)
                title['can_grant'][key] = roles

            results[title['id']] = title

        return results

    def starbases(self):
        """Returns information about the corporation's POSes."""
        api_result = self.api.get('corp/StarbaseList')

        rowset = api_result.find('rowset')
        results = {}
        for row in rowset.findall('row'):
            a = row.attrib
            starbase = {
                'id': int(a['itemID']),
                'type_id': int(a['typeID']),
                'location_id': int(a['locationID']),
                'moon_id': int(a['moonID']),
                'state': constants.Corp.pos_states[int(a['state'])],
                'state_ts': api.parse_ts(a['stateTimestamp']),
                'online_ts': api.parse_ts(a['onlineTimestamp']),
                'standings_owner_id': int(a['standingOwnerID']),
            }
            results[starbase['id']] = starbase

        return results

    def starbase_details(self, starbase_id):
        """Returns details about the specified POS."""
        api_result = self.api.get('corp/StarbaseDetail', {'itemID': starbase_id})

        _str, _int, _float, _bool, _ts = api.elem_getters(api_result)

        general_settings = api_result.find('generalSettings')
        combat_settings = api_result.find('combatSettings')

        def get_fuel_bay_perms(settings):
            # Two 2-bit fields
            usage_flags = int(settings.find('usageFlags').text)
            take_value = usage_flags % 4
            view_value = (usage_flags >> 2) % 4
            return {
                'view': constants.Corp.pos_permission_entities[view_value],
                'take': constants.Corp.pos_permission_entities[take_value],
            }

        def get_deploy_perms(settings):
            # Four 2-bit fields
            deploy_flags = int(settings.find('deployFlags').text)
            anchor_value = (deploy_flags >> 6) % 4
            unanchor_value = (deploy_flags >> 4) % 4
            online_value = (deploy_flags >> 2) % 4
            offline_value = deploy_flags % 4
            return {
                'anchor': constants.Corp.pos_permission_entities[anchor_value],
                'unanchor': constants.Corp.pos_permission_entities[unanchor_value],
                'online': constants.Corp.pos_permission_entities[online_value],
                'offline': constants.Corp.pos_permission_entities[offline_value],
            }

        def get_combat_settings(settings):
            result = {
                'standings_owner_id': int(settings.find('useStandingsFrom').attrib['ownerID']),
                'hostility': {},
            }

            hostility = result['hostility']

            # TODO(ayust): The fields returned by the API don't completely match up with
            # the fields available in-game. May want to revisit this in the future.

            standing = settings.find('onStandingDrop')
            hostility['standing'] = {
                'threshold': float(standing.attrib['standing']) / 100,
                'enabled': standing.attrib.get('enabled') != '0',
            }

            sec_status = settings.find('onStatusDrop')
            hostility['sec_status'] = {
                'threshold': float(sec_status.attrib['standing']) / 100,
                'enabled': sec_status.attrib.get('enabled') != '0',
            }

            hostility['aggression'] = {
                'enabled': settings.find('onAggression').get('enabled') != '0',
            }

            hostility['war'] = {
                'enabled': settings.find('onCorporationWar').get('enabled') != '0',
            }

            return result

        result = {
            'state': constants.Corp.pos_states[_int('state')],
            'state_ts': _ts('stateTimestamp'),
            'online_ts': _ts('onlineTimestamp'),
            'permissions': {
                'fuel': get_fuel_bay_perms(general_settings),
                'deploy': get_deploy_perms(general_settings),
                'forcefield': {
                    'corp': general_settings.find('allowCorporationMembers').text == '1',
                    'alliance': general_settings.find('allowAllianceMembers').text == '1',
                },
            },
            'combat': get_combat_settings(combat_settings),
            'fuel': {},
        }

        rowset = api_result.find('rowset')
        for row in rowset.findall('row'):
            a = row.attrib
            result['fuel'][int(a['typeID'])] = int(a['quantity'])

        return result

    def members(self, extended=True):
        """Returns details about each member of the corporation."""
        api_result = self.api.get('corp/MemberTracking', {'extended': int(extended)})

        rowset = api_result.find('rowset')
        results = {}
        for row in rowset.findall('row'):
            a = row.attrib
            member = {
                'id': int(a['characterID']),
                'name': a['name'],
                'join_ts': api.parse_ts(a['startDateTime']),
                'base': {
                    # TODO(aiiane): Maybe remove this?
                    # It doesn't seem to ever have a useful value.
                    'id': int(a['baseID']),
                    'name': a['base'],
                },
                # Note that title does not include role titles,
                # only ones like 'CEO'
                'title': a['title'],
            }
            if extended:
                member.update({
                    'logon_ts': api.parse_ts(a['logonDateTime']),
                    'logoff_ts': api.parse_ts(a['logoffDateTime']),
                    'location': {
                        'id': int(a['locationID']),
                        'name': a['location'],
                    },
                    'ship_type': {
                        # "Not available" = -1 ship id; we change to None
                        'id': max(int(a['shipTypeID']), 0) or None,
                        'name': a['shipType'] or None,
                    },
                    'roles': int(a['roles']),
                    'can_grant': int(a['grantableRoles']),
                })

            results[member['id']] = member

        return results

    def stations(self):
        """Returns information about the corporation's (non-POS) stations."""
        api_result = self.api.get('corp/OutpostList')

        rowset = api_result.find('rowset')
        results = {}
        for row in rowset.findall('row'):
            a = row.attrib
            station = {
                'id': int(a['stationID']),
                'owner_id': int(a['ownerID']),
                'name': a['stationName'],
                'system_id': int(a['solarSystemID']),
                'docking_fee_per_volume': float(a['dockingCostPerShipVolume']),
                'office_fee': int(a['officeRentalCost']),
                'type_id': int(a['stationTypeID']),
                'reprocessing': {
                    'efficiency': float(a['reprocessingEfficiency']),
                    'cut': float(a['reprocessingStationTake']),
                },
                'standing_owner_id': int(a['standingOwnerID']),
            }
            results[station['id']] = station

        return results


# vim: set ts=4 sts=4 sw=4 et:
