from typing import List
from endstone import Player
from endstone.form import ActionForm, ModalForm, MessageForm, Toggle
from endstone_landclaims.commands.base_handler import BaseHandler
from endstone_landclaims.models.claim import ClaimData

class SettingsHandler(BaseHandler):

    def __init__(self, plugin, config, claim_service, protection_service, spacing_service) -> None:
        super().__init__(plugin, config, claim_service, protection_service)
        self.spacing = spacing_service

    def handle(self, player: Player, args: List[str]) -> bool:
        claim = self._get_claim_at_player(player)

        if not claim:
            player.send_message("§7You are in wilderness (no claim here).")
            return True

        if claim.owner_xuid != int(player.xuid):
            player.send_message("§cOnly the claim owner can access settings.")
            return True

        self._show_main_menu(player, claim.id)
        return True

    def _show_main_menu(self, player: Player, claim_id: str) -> None:
        form = ActionForm(
            title="Claim Settings",
            content="Manage your claim",
        )
        form.add_button("Set Center", on_click=lambda p: self._set_center(p, claim_id))
        form.add_button("Members", on_click=lambda p: self._show_members_list(p, claim_id))
        form.add_button("Permissions", on_click=lambda p: self._show_permissions(p, claim_id))
        player.send_form(form)

    def _set_center(self, player: Player, claim_id: str) -> None:
        claim = self.claim_service.get_claim(claim_id)
        if not claim:
            player.send_message("§cClaim not found.")
            return

        location = player.location
        new_x = int(location.x)
        new_y = int(location.y)
        new_z = int(location.z)
        dimension = self._get_dimension_key(player)
        candidate = ClaimData(
            claim_id="pending",
            owner_xuid=claim.owner_xuid,
            owner_name=claim.owner_name,
            name=claim.name,
            x1=new_x - claim.radius,
            z1=new_z - claim.radius,
            x2=new_x + claim.radius,
            z2=new_z + claim.radius,
            center_y=new_y,
            dimension=dimension,
        )

        other_claims = [c for c in self.claim_service.get_all_claims(dimension) if c.id != claim_id]
        is_valid, reason = self.spacing.validate_claim_creation(candidate, other_claims)

        if not is_valid:
            player.send_message(f"§c{reason}")
            return

        updated = self.claim_service.recenter_claim(claim_id, new_x, new_y, new_z)
        if updated:
            player.send_message("§aClaim center updated to your current position.")
        else:
            player.send_message("§cFailed to update claim center.")

    def _show_members_list(self, player: Player, claim_id: str) -> None:
        claim = self.claim_service.get_claim(claim_id)
        if not claim:
            player.send_message("§cClaim not found.")
            return

        if not claim.basemates:
            player.send_message("§7This claim has no basemates yet.")
            return

        form = ActionForm(title="Members", content="Select a member to view details")
        for xuid in claim.basemates:
            name = self._resolve_name(xuid)
            rank = claim.basemate_ranks.get(xuid, 0)
            rank_label = "Manager" if rank >= 1 else "Member"
            form.add_button(f"{name}\n§7{rank_label}",
                            on_click=lambda p, x=xuid, n=name: self._show_member_detail(p, claim_id, x, n))
        player.send_form(form)

    def _show_member_detail(self, player: Player, claim_id: str, target_xuid: int, target_name: str) -> None:
        claim = self.claim_service.get_claim(claim_id)
        if not claim:
            player.send_message("§cClaim not found.")
            return
        rank = claim.basemate_ranks.get(target_xuid, 0)
        rank_label = "Manager" if rank >= 1 else "Member"
        is_online = any(int(o.xuid) == target_xuid for o in self.plugin.server.online_players)
        status = "§aOnline" if is_online else "§7Offline"
        content = f"§7Name: §e{target_name}\n§7Rank: §e{rank_label}\n§7Status: {status}"
        form = ActionForm(title=target_name, content=content)
        form.add_button("Kick from Claim", on_click=lambda p: self._confirm_kick(p, claim_id, target_xuid, target_name))
        form.add_button("Back", on_click=lambda p: self._show_members_list(p, claim_id))
        player.send_form(form)

    def _confirm_kick(self, player: Player, claim_id: str, target_xuid: int, target_name: str) -> None:
        def on_submit(p: Player, button_index: int) -> None:
            if button_index == 0:
                if self.claim_service.remove_basemate(claim_id, target_xuid):
                    self.claim_service.release_player_contributions(claim_id, target_xuid)
                    p.send_message(f"§aKicked {target_name} from the claim.")
                else:
                    p.send_message(f"§cFailed to kick {target_name}.")

        form = MessageForm(
            title="Confirm Kick",
            content=f"Are you sure you want to kick {target_name}?",
            button1="Yes",
            button2="No",
            on_submit=on_submit,
        )
        player.send_form(form)

    def _show_permissions(self, player: Player, claim_id: str) -> None:
        claim = self.claim_service.get_claim(claim_id)
        if not claim:
            player.send_message("§cClaim not found.")
            return

        def on_submit(p: Player, data_json: str) -> None:
            import json
            try:
                data = json.loads(data_json)
                allow_pvp = bool(data[0])
                self.claim_service.set_claim_permissions(claim_id, allow_pvp=allow_pvp)
                p.send_message("§aPermissions updated.")
            except Exception:
                p.send_message("§cFailed to update permissions.")

        form = ModalForm(
            title="Claim Permissions",
            controls=[
                Toggle("Allow PvP", default_value=claim.permissions.get("allow_pvp", False)),
            ],
            submit_button="Save",
            on_submit=on_submit,
        )
        player.send_form(form)

    def _resolve_name(self, xuid: int) -> str:
        for online in self.plugin.server.online_players:
            if int(online.xuid) == xuid:
                return online.name

        record = self.claim_service.db.get_player_by_xuid(xuid)
        if record:
            return record["name"]

        return f"Unknown ({xuid})"