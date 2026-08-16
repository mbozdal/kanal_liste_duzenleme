#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TCL Channel Editor
------------------
A small Windows-friendly Tkinter GUI for TCL/Thomson channel-list TAR exports.

Based on the publicly available ChanSort TCL loader design:
- TAR contains database/cloneCRC.bin
- database/userdata/DtvData.db
- database/userdata/satellite.db
- ServiceName is stored as a 64-byte UTF-8 BLOB
- cloneCRC.bin bytes 2..3 contain little-endian CRC16-CCITT of
  min(len(DtvData.db), 0x4B000) bytes
- bytes 4..5 contain the satellite.db CRC in the format used by ChanSort;
  this editor does not modify satellite.db, so its CRC is preserved.

The program intentionally changes only channel number/name/edit flags and
the DtvData CRC. The original TAR is never overwritten.
"""

import os
import csv
import shutil
import sqlite3
import struct
import tarfile
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path


CRC_MAX_DATA_LENGTH = 0x4B000
KNOWN_EDIT_FLAGS = 0x01 | 0x02 | 0x08 | 0x10  # Favorite, CustomProgNum, Hidden, Delete


def crc16_ccitt(data: bytes, init: int = 0xFFFF) -> int:
    """CRC16-CCITT used by ChanSort's TCL loader."""
    crc = init
    for b in data:
        crc ^= b << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def decode_blob_name(value) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value.rstrip("\x00 ")
    raw = bytes(value)
    raw = raw.split(b"\x00", 1)[0]
    return raw.decode("utf-8", errors="replace").rstrip(" ")


def encode_blob_name(name: str) -> bytes:
    raw = name.encode("utf-8")
    if len(raw) > 64:
        raw = raw[:64]
        # Avoid cutting a UTF-8 sequence.
        while True:
            try:
                raw.decode("utf-8")
                break
            except UnicodeDecodeError:
                raw = raw[:-1]
    return raw + bytes(64 - len(raw))


def safe_extract(tar: tarfile.TarFile, destination: Path):
    """Extract only regular files/directories and prevent path traversal."""
    root = destination.resolve()
    for member in tar.getmembers():
        target = (destination / member.name).resolve()
        if not str(target).startswith(str(root) + os.sep) and target != root:
            raise ValueError(f"Unsafe TAR member path: {member.name}")
        if member.isdir():
            target.mkdir(parents=True, exist_ok=True)
        elif member.isfile():
            target.parent.mkdir(parents=True, exist_ok=True)
            src = tar.extractfile(member)
            if src is None:
                raise ValueError(f"Cannot extract {member.name}")
            with open(target, "wb") as f:
                shutil.copyfileobj(src, f)
            try:
                os.chmod(target, member.mode & 0o7777)
            except OSError:
                pass
            try:
                os.utime(target, (member.mtime, member.mtime))
            except OSError:
                pass
        # Ignore special members. TCL exports are expected to contain normal
        # files/directories.


def find_member(base: Path, filename: str) -> Path | None:
    candidates = [
        base / "database" / filename,
        base / filename,
        base / "userdata" / filename,
        base / "database" / "userdata" / filename,
    ]
    for p in candidates:
        if p.is_file():
            return p

    for p in base.rglob(filename):
        if p.is_file():
            return p
    return None


class TclArchive:
    def __init__(self):
        self.tempdir = None
        self.root = None
        self.dtv = None
        self.satellite = None
        self.crcfile = None
        self.original_tar = None
        self.members = []
        self.member_data = {}

    def close(self):
        if self.tempdir:
            shutil.rmtree(self.tempdir, ignore_errors=True)
        self.tempdir = None
        self.root = None

    def open_tar(self, filename):
        self.close()
        self.original_tar = Path(filename)

        self.tempdir = Path(tempfile.mkdtemp(prefix="tcl_channel_editor_"))
        self.root = self.tempdir / "extract"
        self.root.mkdir()

        with tarfile.open(filename, "r:*") as tar:
            self.members = tar.getmembers()
            safe_extract(tar, self.root)

        self.dtv = find_member(self.root, "DtvData.db")
        self.satellite = find_member(self.root, "satellite.db")
        self.crcfile = find_member(self.root, "cloneCRC.bin")

        if self.dtv is None:
            raise ValueError("TAR içinde DtvData.db bulunamadı.")
        if self.crcfile is None:
            raise ValueError("TAR içinde cloneCRC.bin bulunamadı.")

    def read_channels(self):
        con = sqlite3.connect(self.dtv)
        con.row_factory = sqlite3.Row
        try:
            cur = con.execute("""
                SELECT
                    p.u32Index AS db_index,
                    p.ProgNum AS prog_num,
                    p.ServiceID AS service_id,
                    p.ServiceName AS service_name,
                    p.ShortServiceName AS short_name,
                    p.LCN AS lcn,
                    p.VideoType AS video_type,
                    p.EditFlag AS edit_flag,
                    p.u8DtvRoute AS route,
                    a.IsDelete AS is_delete,
                    a.IsSkipped AS is_skipped,
                    a.IsLock AS is_lock,
                    a.IsFavor AS is_favor,
                    a.IsRename AS is_rename
                FROM PrograminfoTbl p
                LEFT JOIN AtrributeTbl a ON a.u32Index = p.u32Index
                ORDER BY
                    CASE WHEN p.ProgNum = 65535 THEN 1 ELSE 0 END,
                    p.ProgNum,
                    p.u32Index
            """)
            rows = []
            for r in cur.fetchall():
                rows.append({
                    "db_index": r["db_index"],
                    "prog_num": r["prog_num"],
                    "service_id": r["service_id"],
                    "name": decode_blob_name(r["service_name"]),
                    "short_name": decode_blob_name(r["short_name"]),
                    "lcn": r["lcn"],
                    "video_type": r["video_type"],
                    "edit_flag": r["edit_flag"] or 0,
                    "is_delete": r["is_delete"] or 0,
                    "is_skipped": r["is_skipped"] or 0,
                    "is_lock": r["is_lock"] or 0,
                    "is_favor": r["is_favor"] or 0,
                    "is_rename": r["is_rename"] or 0,
                })
            return rows
        finally:
            con.close()

    def verify_crc(self):
        data = self.dtv.read_bytes()
        actual = crc16_ccitt(data[:min(len(data), CRC_MAX_DATA_LENGTH)])
        raw = self.crcfile.read_bytes()
        if len(raw) < 6:
            return False, actual, None
        expected = struct.unpack_from("<H", raw, 2)[0]
        return actual == expected, actual, expected

    def update_crc(self):
        data = self.dtv.read_bytes()
        crc = crc16_ccitt(data[:min(len(data), CRC_MAX_DATA_LENGTH)])
        raw = bytearray(self.crcfile.read_bytes())
        if len(raw) < 6:
            raise ValueError("cloneCRC.bin 6 byte'tan kısa.")
        struct.pack_into("<H", raw, 2, crc)
        self.crcfile.write_bytes(raw)
        return crc

    def save_tar(self, output_filename):
        output = Path(output_filename)
        if output.resolve() == self.original_tar.resolve():
            raise ValueError("Orijinal TAR'ın üzerine yazmak güvenlik nedeniyle engellendi.")

        # GNU_FORMAT is intentional: TCL exports are old-GNU tar style and
        # ChanSort uses a custom GNU tar implementation for this reason.
        with tarfile.open(output, "w", format=tarfile.GNU_FORMAT) as out:
            for member in self.members:
                src = self.root / member.name

                # Re-create metadata from the original TAR header.
                info = tarfile.TarInfo(member.name)
                info.mode = member.mode
                info.uid = member.uid
                info.gid = member.gid
                info.mtime = member.mtime
                info.uname = member.uname
                info.gname = member.gname
                info.type = member.type
                info.linkname = member.linkname
                info.pax_headers = dict(member.pax_headers)

                if member.isdir():
                    out.addfile(info)
                elif member.isfile():
                    info.size = src.stat().st_size
                    with open(src, "rb") as f:
                        out.addfile(info, f)

        return output


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("TCL Channel Editor - TAR")
        self.geometry("1250x760")
        self.minsize(950, 600)

        self.archive = TclArchive()
        self.rows = []
        self.dirty = False
        self.drag_item = None
        self.drag_start_y = 0
        self.dragging = False
        self.sort_column = None
        self.sort_reverse = False

        self._build_ui()
        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def _build_ui(self):
        top = ttk.Frame(self, padding=8)
        top.pack(fill="x")

        ttk.Button(top, text="TAR Aç", command=self.open_tar).pack(side="left", padx=3)
        ttk.Button(top, text="Kaydet / TAR Oluştur", command=self.save_tar).pack(side="left", padx=3)
        ttk.Button(top, text="CRC Kontrol", command=self.check_crc).pack(side="left", padx=3)
        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(top, text="▲ Yukarı", command=lambda: self.move_selected(-1)).pack(side="left", padx=2)
        ttk.Button(top, text="▼ Aşağı", command=lambda: self.move_selected(1)).pack(side="left", padx=2)
        ttk.Button(top, text="1..N Yeniden Numarala", command=self.renumber).pack(side="left", padx=2)
        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(top, text="CSV İçe Aktar", command=self.import_csv).pack(side="left", padx=2)
        ttk.Button(top, text="CSV Dışa Aktar", command=self.export_csv).pack(side="left", padx=2)
        ttk.Separator(top, orient="vertical").pack(side="left", fill="y", padx=6)

        ttk.Label(top, text="Sırala:").pack(side="left", padx=(2, 3))
        self.sort_var = tk.StringVar(value="Yeni No")
        self.sort_combo = ttk.Combobox(
            top, textvariable=self.sort_var,
            values=["Yeni No", "Eski No", "Kanal Adı", "Service ID", "LCN"],
            state="readonly", width=13
        )
        self.sort_combo.pack(side="left", padx=2)
        self.sort_order_var = tk.StringVar(value="Artan")
        ttk.Combobox(
            top, textvariable=self.sort_order_var,
            values=["Artan", "Azalan"], state="readonly", width=8
        ).pack(side="left", padx=2)
        ttk.Button(top, text="Uygula", command=self.apply_sort).pack(side="left", padx=2)

        ttk.Button(top, text="Değişiklikleri Geri Al", command=self.reload).pack(side="left", padx=3)

        self.file_label = ttk.Label(top, text="TAR seçilmedi")
        self.file_label.pack(side="left", padx=15)

        search_frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        search_frame.pack(fill="x")

        ttk.Label(search_frame, text="Ara:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ttk.Entry(search_frame, textvariable=self.search_var, width=35).pack(side="left", padx=5)

        self.status = ttk.Label(search_frame, text="0 kanal")
        self.status.pack(side="right")

        frame = ttk.Frame(self, padding=(8, 0, 8, 8))
        frame.pack(fill="both", expand=True)

        columns = ("new", "old", "name", "sid", "lcn", "type", "fav", "hide", "lock")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        headings = {
            "new": "Yeni No",
            "old": "Eski No",
            "name": "Kanal Adı",
            "sid": "Service ID",
            "lcn": "LCN",
            "type": "Video",
            "fav": "Fav",
            "hide": "Gizli",
            "lock": "Kilit",
        }
        widths = {
            "new": 80, "old": 80, "name": 300, "sid": 90, "lcn": 80,
            "type": 70, "fav": 55, "hide": 55, "lock": 55
        }
        for c in columns:
            self.tree.heading(c, text=headings[c])
            self.tree.column(c, width=widths[c], anchor="center" if c != "name" else "w")

        vs = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hs = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vs.set, xscrollcommand=hs.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vs.grid(row=0, column=1, sticky="ns")
        hs.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

        self.tree.bind("<Double-1>", self.edit_cell)
        self.tree.bind("<F2>", self.edit_cell)
        self.tree.bind("<ButtonPress-1>", self.drag_start)
        self.tree.bind("<B1-Motion>", self.drag_motion)
        self.tree.bind("<ButtonRelease-1>", self.drag_drop)

        bottom = ttk.Frame(self, padding=8)
        bottom.pack(fill="x")
        ttk.Label(
            bottom,
            text="Çift tıklama: düzenle | Sürükle-bırak: yeniden sırala | Sütun başlığı: sırala | Yeni No benzersiz olmalı"
        ).pack(side="left")

    def open_tar(self):
        filename = filedialog.askopenfilename(
            title="TCL TAR kanal listesini seç",
            filetypes=[("TCL TAR", "*.tar"), ("Tüm dosyalar", "*.*")]
        )
        if not filename:
            return
        try:
            self.archive.open_tar(filename)
            self.rows = self.archive.read_channels()
            self.dirty = False
            self.file_label.config(text=str(filename))
            self.refresh()
            ok, actual, expected = self.archive.verify_crc()
            if expected is None:
                self.status.config(text=f"{len(self.rows)} kanal | CRC okunamadı")
            else:
                state = "CRC OK" if ok else "CRC HATALI"
                self.status.config(text=f"{len(self.rows)} kanal | {state} | {actual:04X}")
        except Exception as e:
            self.archive.close()
            messagebox.showerror("Açma hatası", str(e))

    def reload(self):
        if not self.archive.original_tar:
            return
        if self.dirty and not messagebox.askyesno("Geri al", "Kaydedilmemiş değişiklikler silinsin mi?"):
            return
        try:
            fn = self.archive.original_tar
            self.archive.open_tar(fn)
            self.rows = self.archive.read_channels()
            self.dirty = False
            self.refresh()
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def refresh(self):
        q = self.search_var.get().strip().lower()
        for item in self.tree.get_children():
            self.tree.delete(item)

        shown = 0
        for i, r in enumerate(self.rows):
            text = f"{r['name']} {r['service_id']} {r['prog_num']}".lower()
            if q and q not in text:
                continue

            new_no = r.get("new_no", r["prog_num"])
            if new_no == 65535:
                new_text = "-"
            else:
                new_text = str(new_no)

            vtype = {1: "SD", 4: "HD", 6: "UHD"}.get(r["video_type"], str(r["video_type"]))
            self.tree.insert(
                "", "end", iid=str(i),
                values=(
                    new_text,
                    "-" if r["prog_num"] == 65535 else r["prog_num"],
                    r["name"],
                    r["service_id"],
                    r["lcn"] if r["lcn"] is not None else "",
                    vtype,
                    "Evet" if r["is_favor"] or (r["edit_flag"] & 0x01) else "",
                    "Evet" if r["is_skipped"] or (r["edit_flag"] & 0x08) else "",
                    "Evet" if r["is_lock"] else "",
                )
            )
            shown += 1

        self.status.config(text=f"{shown}/{len(self.rows)} kanal")

    def validate_unique_numbers(self, show_error=True):
        """Ensure every active channel has a unique New No."""
        seen = {}
        duplicates = []
        for r in self.rows:
            if r["prog_num"] == 65535 or r.get("is_delete"):
                continue
            n = r.get("new_no", r["prog_num"])
            if n in seen:
                duplicates.append((n, seen[n]["name"], r["name"]))
            else:
                seen[n] = r

        if duplicates:
            if show_error:
                details = "\n".join(
                    f"{n}: {a} / {b}" for n, a, b in duplicates[:12]
                )
                more = "" if len(duplicates) <= 12 else f"\n... ve {len(duplicates)-12} tekrar daha"
                messagebox.showerror(
                    "Tekrarlanan kanal numarası",
                    "Yeni No değerleri benzersiz olmalıdır.\n\n"
                    + details + more
                )
            return False
        return True

    def apply_sort(self):
        if not self.rows:
            return

        colmap = {
            "Yeni No": "new",
            "Eski No": "old",
            "Kanal Adı": "name",
            "Service ID": "sid",
            "LCN": "lcn",
        }
        col = colmap[self.sort_var.get()]
        reverse = self.sort_order_var.get() == "Azalan"
        self.sort_by_column(col, reverse)

    def sort_by_column(self, col, forced_reverse=False):
        """Sort the actual backing list, then redraw the grid."""
        if not self.rows:
            return

        def val(r):
            if col == "new":
                return r.get("new_no", r["prog_num"])
            if col == "old":
                return r["prog_num"]
            if col == "name":
                return r["name"].casefold()
            if col == "sid":
                return r["service_id"] if r["service_id"] is not None else -1
            if col == "lcn":
                return r["lcn"] if r["lcn"] is not None else -1
            return 0

        # Stable sort; unassigned 65535 entries stay at the end.
        if col in ("new", "old"):
            assigned = [r for r in self.rows if r["prog_num"] != 65535]
            unassigned = [r for r in self.rows if r["prog_num"] == 65535]
            assigned.sort(key=val, reverse=forced_reverse)
            self.rows[:] = assigned + unassigned
        else:
            self.rows.sort(key=val, reverse=forced_reverse)

        self.sort_column = col
        self.sort_reverse = forced_reverse
        self.dirty = True
        self.refresh()

    def export_csv(self):
        if not self.rows:
            messagebox.showwarning("CSV", "Önce bir TAR dosyası açın.")
            return

        filename = filedialog.asksaveasfilename(
            title="Kanal listesini CSV olarak kaydet",
            defaultextension=".csv",
            initialfile="tcl_channels.csv",
            filetypes=[("CSV", "*.csv")]
        )
        if not filename:
            return

        fields = [
            "New_No", "Old_No", "Channel_Name", "Service_ID", "LCN",
            "DB_Index", "Video_Type", "EditFlag", "Favorite",
            "Skipped", "Locked", "Deleted"
        ]

        try:
            with open(filename, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.DictWriter(f, fieldnames=fields)
                w.writeheader()
                for r in self.rows:
                    w.writerow({
                        "New_No": r.get("new_no", r["prog_num"]),
                        "Old_No": r["prog_num"],
                        "Channel_Name": r["name"],
                        "Service_ID": r["service_id"],
                        "LCN": r["lcn"] if r["lcn"] is not None else "",
                        "DB_Index": r["db_index"],
                        "Video_Type": r["video_type"],
                        "EditFlag": r["edit_flag"],
                        "Favorite": int(bool(r["is_favor"] or (r["edit_flag"] & 0x01))),
                        "Skipped": int(bool(r["is_skipped"] or (r["edit_flag"] & 0x08))),
                        "Locked": int(bool(r["is_lock"])),
                        "Deleted": int(bool(r["is_delete"])),
                    })
            messagebox.showinfo("CSV", f"CSV dışa aktarıldı:\n{filename}")
        except Exception as e:
            messagebox.showerror("CSV dışa aktarma hatası", str(e))

    def import_csv(self):
        if not self.rows:
            messagebox.showwarning("CSV", "Önce bir TAR dosyası açın.")
            return

        filename = filedialog.askopenfilename(
            title="Kanal CSV dosyasını seç",
            filetypes=[("CSV", "*.csv"), ("Tüm dosyalar", "*.*")]
        )
        if not filename:
            return

        try:
            with open(filename, "r", newline="", encoding="utf-8-sig") as f:
                records = list(csv.DictReader(f))

            if not records:
                raise ValueError("CSV boş.")

            # Match primarily by Service_ID; this survives channel-number changes.
            by_sid = {str(r["service_id"]): r for r in self.rows if r["service_id"] is not None}

            changed = 0
            for rec in records:
                sid = rec.get("Service_ID", "").strip()
                if not sid or sid not in by_sid:
                    continue
                r = by_sid[sid]

                if rec.get("New_No", "").strip():
                    n = int(rec["New_No"])
                    if not 1 <= n <= 65534:
                        raise ValueError(f"Geçersiz New_No: {n}")
                    r["new_no"] = n

                if "Channel_Name" in rec and rec["Channel_Name"] != "":
                    r["name"] = rec["Channel_Name"]
                    r["is_rename"] = 1

                changed += 1

            if not self.validate_unique_numbers(show_error=True):
                return

            self.dirty = True
            self.refresh()
            messagebox.showinfo("CSV", f"{changed} kanal güncellendi.")
        except Exception as e:
            messagebox.showerror("CSV içe aktarma hatası", str(e))

    def drag_start(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.drag_item = None
            return
        self.drag_item = item
        self.drag_start_y = event.y
        self.dragging = False
        self.tree.selection_set(item)
        self.tree.focus(item)

    def drag_motion(self, event):
        if not self.drag_item:
            return
        if abs(event.y - self.drag_start_y) >= 5:
            self.dragging = True
        target = self.tree.identify_row(event.y)
        if target:
            self.tree.selection_set(target)

    def drag_drop(self, event):
        if not self.drag_item or not self.dragging:
            self.drag_item = None
            return

        source_iid = self.drag_item
        target_iid = self.tree.identify_row(event.y)
        self.drag_item = None
        self.dragging = False

        if not target_iid or source_iid == target_iid:
            return

        if self.search_var.get().strip():
            messagebox.showwarning("Filtre açık", "Çek-bırak için filtreyi temizleyin.")
            return

        try:
            src = int(source_iid)
            dst = int(target_iid)
        except ValueError:
            return

        if src == dst or not (0 <= src < len(self.rows)) or not (0 <= dst < len(self.rows)):
            return

        row = self.rows.pop(src)
        if src < dst:
            dst -= 1

        bbox = self.tree.bbox(target_iid)
        if bbox and event.y > bbox[1] + bbox[3] / 2:
            dst += 1

        dst = max(0, min(dst, len(self.rows)))
        self.rows.insert(dst, row)

        self.assign_sequential_numbers()
        self.sort_column = None
        self.dirty = True
        self.refresh()

    def move_selected(self, delta):
        selection = self.tree.selection()
        if not selection:
            messagebox.showinfo("Kanal seç", "Önce bir kanal seçin.")
            return
        if self.search_var.get().strip():
            messagebox.showwarning("Filtre açık", "Taşıma için filtreyi temizleyin.")
            return

        idx = int(selection[0])
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(self.rows):
            return

        self.rows[idx], self.rows[new_idx] = self.rows[new_idx], self.rows[idx]
        self.assign_sequential_numbers()
        self.sort_column = None
        self.dirty = True
        self.refresh()

        if str(new_idx) in self.tree.get_children():
            self.tree.selection_set(str(new_idx))
            self.tree.focus(str(new_idx))
            self.tree.see(str(new_idx))

    def assign_sequential_numbers(self):
        active = [
            r for r in self.rows
            if r["prog_num"] != 65535 and not r.get("is_delete")
        ]
        for n, r in enumerate(active, 1):
            r["new_no"] = n

    def edit_cell(self, event=None):
        item = self.tree.identify_row(event.y) if event else self.tree.focus()
        col = self.tree.identify_column(event.x) if event else "#1"
        if not item:
            return
        idx = int(item)
        row = self.rows[idx]

        if col not in ("#1", "#3"):
            return

        bbox = self.tree.bbox(item, col)
        if not bbox:
            return

        x, y, w, h = bbox
        value = row.get("new_no", row["prog_num"]) if col == "#1" else row["name"]

        editor = ttk.Entry(self.tree)
        editor.place(x=x, y=y, width=w, height=h)
        editor.insert(0, "" if value == 65535 else str(value))
        editor.select_range(0, "end")
        editor.focus_set()

        def commit(_=None):
            try:
                text = editor.get().strip()
                if col == "#1":
                    if not text:
                        raise ValueError("Kanal numarası boş bırakılamaz.")
                    number = int(text)
                    if number < 1 or number > 65534:
                        raise ValueError("Kanal numarası 1..65534 aralığında olmalı.")
                    # Check immediately against the other active channels.
                    for other in self.rows:
                        if other is row or other["prog_num"] == 65535 or other.get("is_delete"):
                            continue
                        if other.get("new_no", other["prog_num"]) == number:
                            raise ValueError(
                                f"{number} zaten '{other['name']}' kanalına atanmış."
                            )
                    row["new_no"] = number
                else:
                    if len(text.encode("utf-8")) > 64:
                        raise ValueError("Kanal adı UTF-8 olarak en fazla 64 byte olabilir.")
                    row["name"] = text
                    row["is_rename"] = 1
                self.dirty = True
                editor.destroy()
                self.refresh()
            except Exception as e:
                messagebox.showerror("Geçersiz değer", str(e))
                editor.focus_set()

        editor.bind("<Return>", commit)
        editor.bind("<Escape>", lambda *_: editor.destroy())
        editor.bind("<FocusOut>", commit)

    def renumber(self):
        if not self.rows:
            return
        self.assign_sequential_numbers()
        self.dirty = True
        self.sort_column = None
        self.refresh()

    def apply_changes(self):
        if not self.rows:
            return

        con = sqlite3.connect(self.archive.dtv)
        try:
            cur = con.cursor()
            con.execute("BEGIN")

            for r in self.rows:
                new_no = r.get("new_no", r["prog_num"])
                if new_no == 65535:
                    continue

                # Preserve unknown edit bits, while rebuilding the flags
                # handled by ChanSort's TCL serializer.
                old_flags = int(r["edit_flag"] or 0)
                flags = old_flags & ~KNOWN_EDIT_FLAGS

                if r["is_favor"] or (old_flags & 0x01):
                    flags |= 0x01
                if r["is_skipped"] or (old_flags & 0x08):
                    flags |= 0x08
                if r["is_delete"]:
                    flags |= 0x10
                else:
                    flags |= 0x02  # custom/moved program number

                cur.execute(
                    """
                    UPDATE PrograminfoTbl
                    SET ProgNum=?, ServiceName=?, EditFlag=?
                    WHERE u32Index=?
                    """,
                    (int(new_no), encode_blob_name(r["name"]), flags, int(r["db_index"]))
                )

                cur.execute(
                    """
                    UPDATE AtrributeTbl
                    SET IsRename=?
                    WHERE u32Index=?
                    """,
                    (int(r["is_rename"]), int(r["db_index"]))
                )

            con.commit()
        except Exception:
            con.rollback()
            raise
        finally:
            con.close()

        self.archive.update_crc()

    def save_tar(self):
        if not self.archive.original_tar:
            messagebox.showwarning("Dosya yok", "Önce bir TCL TAR dosyası açın.")
            return
        if not self.dirty:
            messagebox.showinfo("Değişiklik yok", "Kaydedilecek değişiklik yok.")
            return

        out = filedialog.asksaveasfilename(
            title="Yeni TCL TAR kaydet",
            defaultextension=".tar",
            initialfile=self.archive.original_tar.stem + "_edited.tar",
            filetypes=[("TCL TAR", "*.tar"), ("Tüm dosyalar", "*.*")]
        )
        if not out:
            return

        try:
            if not self.validate_unique_numbers(show_error=True):
                return

            # Work on extracted copy. The source TAR is untouched.
            self.apply_changes()
            self.archive.save_tar(out)

            self.dirty = False
            ok, actual, expected = self.archive.verify_crc()
            messagebox.showinfo(
                "Tamamlandı",
                f"Yeni TAR oluşturuldu:\n{out}\n\n"
                f"DtvData CRC16-CCITT: {actual:04X}\n"
                f"cloneCRC.bin değeri: {expected:04X}\n"
                f"CRC durumu: {'OK' if ok else 'HATALI'}"
            )
            self.file_label.config(text=out)
        except Exception as e:
            messagebox.showerror("Kaydetme hatası", str(e))

    def check_crc(self):
        if not self.archive.dtv:
            messagebox.showwarning("Dosya yok", "Önce bir TAR açın.")
            return
        try:
            ok, actual, expected = self.archive.verify_crc()
            if expected is None:
                messagebox.showwarning("CRC", "cloneCRC.bin okunamadı.")
            else:
                messagebox.showinfo(
                    "CRC16-CCITT",
                    f"Hesaplanan: {actual:04X}\n"
                    f"cloneCRC.bin: {expected:04X}\n\n"
                    f"{'CRC UYUMLU' if ok else 'CRC UYUMSUZ'}"
                )
        except Exception as e:
            messagebox.showerror("CRC hatası", str(e))

    def on_close(self):
        if self.dirty:
            ans = messagebox.askyesnocancel(
                "Çıkış", "Kaydedilmemiş değişiklikler var. Çıkmak istiyor musunuz?"
            )
            if ans is None:
                return
        self.archive.close()
        self.destroy()


if __name__ == "__main__":
    App().mainloop()
