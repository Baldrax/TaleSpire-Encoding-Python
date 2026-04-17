# Encoding Schemes for TS:
# https://talespire.com/url-scheme
from __future__ import annotations

import gzip
import struct
import pyperclip

try:
    from ts_encoding.common import TSCodingBase
except ModuleNotFoundError:
    from common import TSCodingBase

from pprint import pprint

class TSSlab(TSCodingBase):
    """
    A Class to Decode and Encode a TaleSpire Slab.
    """

    def __init__(self):
        super().__init__()
        self._layout_count = 0
        self._force_version = None

    def _init_data(self):
        self.data = {
            "magic_num": 3520002766,
            "version": 2,
            "layout_count": 0,
            "num_creatures": 0,
            "layouts": [],
        }

    def decode_slab(self, slab_str):
        self._code = slab_str.encode("ascii")
        self._decode()

    def _decode_steps(self):
        self._binary_data = gzip.decompress(self._binary_data) # Unzip the data

        self.data["magic_num"] = self._unpack_u32()
        self._version = self._unpack_u16()  # Unpack the version of the slab so we know which schema to use.
        self.data["version"] = self._version
        self._layout_count = self._unpack_u16()
        self.data["layout_count"] = self._layout_count

        if self._version > 1:
            self.data["num_creatures"] = self._unpack_u16()  # Number of Creatures is in v2 and higher.
        self._decode_layouts()

        if self._version == 1:
            self._decode_instances_v1()
        else:
            self._decode_instances_v2()

    def _decode_layouts(self):
        for n in range(self._layout_count):
            uuid = self._unpack_slab_uuid()
            asset_count = self._unpack_u16()
            reserved = self._unpack_u16()
            self.data["layouts"].append(
                {
                    "uuid": uuid,
                    "instance_count": asset_count,
                    "reserved": reserved,
                    "instances": []
                }
            )

    def _decode_instances_v1(self):
        for asset in self.data["layouts"]:
            for n in range(asset["instance_count"]):
                pos = struct.unpack_from("<3f", self._binary_data, self._offset)  # 3 floats
                self._offset += 12

                size = struct.unpack_from("<3f", self._binary_data, self._offset)  # 3 floats
                self._offset += 12

                rot = self._unpack_u8()

                self._offset += 3  # For ignored data

                instance_data = {
                    "pos_x": pos[0],
                    "pos_y": pos[1],
                    "pos_z": pos[2],
                    "size_x": size[0],
                    "size_y": size[1],
                    "size_z": size[2],
                    "degrees": rot * 22.5
                }
                asset["instances"].append(instance_data)

    def _decode_instances_v2(self):
        for asset in self.data["layouts"]:
            for n in range(asset["instance_count"]):
                packed_transform = self._unpack_u64()
                unused = (packed_transform >> 59) & 0b11111
                rot = (packed_transform >> 54) & 0b11111
                pos_x = (packed_transform >> 36) & 0x3FFFF
                pos_y = (packed_transform >> 18) & 0x3FFFF
                pos_z = packed_transform & 0x3FFFF
                instance_data = {
                    "degrees": rot * 15.0,
                    "pos_x": pos_x / 100.0,
                    "pos_y": pos_y / 100.0,
                    "pos_z": pos_z / 100.0
                }
                asset["instances"].append(instance_data)

    def encode_slab(self, force_version: int | None = None):
        if force_version:
            self._force_version = force_version
        self._encode()
        return self._code.decode("ascii")

    def _encode_steps(self) -> None:
        """
        The steps to encode the data.
        Each step is broken down to a single line or method for ease of debugging and updating the schema.
        After this is run the entire blueprint should be encoded and stored in `self.binary_data`.
        """
        self._pack_u32(self.data["magic_num"])
        if self._force_version:
            self._version = self._force_version
        else:
            self._version = self.data["version"]

        self._pack_u16(self._version)
        self._pack_u16(self.data["layout_count"])

        if self._version > 1:
            self._pack_u16(self.data["num_creatures"])

        self._encode_layouts()

        if self._version == 1:
            self._encode_instances_v1()
        else:
            self._encode_instances_v2()

        self._binary_data = gzip.compress(self._binary_data, compresslevel=9)

    def _encode_layouts(self):
        for layout in self.data["layouts"]:
            uuid_str = layout["uuid"]
            if "reserved" in layout.keys():
                reserved = layout["reserved"]
            else:
                reserved = 0
            instance_count = len(layout["instances"])
            self._pack_slab_uuid(uuid_str)
            self._pack_u16(instance_count)
            self._pack_u16(reserved)

    def _encode_instances_v1(self):
        for asset in self.data["layouts"]:
            for data in asset["instances"]:
                pos = (data["pos_x"], data["pos_y"], data["pos_z"])
                size = (data["size_x"], data["size_y"], data["size_z"])
                rot = int(data["degrees"]/22.5)

                self._binary_data.extend(struct.pack("<3f", *pos))
                self._binary_data.extend(struct.pack("<3f", *size))
                self._pack_u8(rot)
                self._binary_data.extend(struct.pack("3x"))  # 3 bytes of empty data

    def _encode_instances_v2(self):
        offset_x = offset_y = offset_z = 0
        if self.data["version"] == 1:
            min_x = min_y = min_z = 0
            for asset in self.data["layouts"]:
                for data in asset["instances"]:
                    min_x = min(min_x, data["pos_x"])
                    min_y = min(min_y, data["pos_y"])
                    min_z = min(min_z, data["pos_z"])
            offset_x = abs(min_x)
            offset_y = abs(min_y)
            offset_z = abs(min_z)

        print(offset_x, offset_y, offset_z)

        for asset in self.data["layouts"]:
            for data in asset["instances"]:
                unused = 0
                rot = int(data["degrees"] / 15) & 0b11111
                pos_x = int((data["pos_x"] + offset_x) * 100) & 0x3FFFF
                pos_y = int((data["pos_y"] + offset_y) * 100) & 0x3FFFF
                pos_z = int((data["pos_z"] + offset_z) * 100) & 0x3FFFF
                if  pos_z > 10000:
                    print(data["pos_z"])
                    print(pos_z)

                packed = (
                    (unused << 59) |
                    (rot << 54) |
                    (pos_x << 36) |
                    (pos_y << 18) |
                    pos_z
                )
                self._pack_u64(packed)

# TODO: Remove this before merging into main. Maybe move some into unit testing.
if __name__ == "__main__":
    test_slab_v02 =\
        ("H4sIAAAAAAAACsVZf3Rc1XG+b997q0Ve25J3bWllSbuyLerGmxyOopINoeoCMoZoTXBwkZIYIpJNILXaqISmG0rDk1EIPnFgk2NUEdRgZHGq"
         "hDTaggGDlrDGNllKqigHkeOqG7BIqbeAetxYSYnjpp1vZh5Kmv7Z0/z1nZl379y5c+fOj/tmzs78IGDixpi68aPWL/Y/0L1v231d811/en6Ie"
         "Lf/S03gqd2PXnXwsp3PvHP7771oES/8iz3u7AN/eNn9b+2p+503v7vdJt7Xb3xrjblhfPvBpw+ee7794QvqiTd3/bnok5et6fFu2HWw6RanFX"
         "MvXPiDzUeb2tNPPpO/IXl55oMriNfw/Lve2fLg726/73Ovfiwb/OjfQ97KH9S/d0v03R944PXrLqo7/p6hu4n3jb/76XvXfTyyPf/DNQeeev7"
         "o3W8Qb8snLtm2dePEld956aLbn/rX9Z/fRryze67dcellJ7YO/ejRlrPtr+Wxj2Dk59d8pyOS8W791LU/qf+n4+uIN9y26mN7s/Xddz654aKj"
         "fc/1QL94oOPG2E9fv/RvrFWvbivc9ifvJt7vP3b0pg+tfW7rwfDLf/ye3rV/hnF3brz1qz/Mfu3SR3N7nnHfsfJFrPFGPL5/26vjV9x/4a7Pv"
         "/LQhZ/aQQOne16896v3b+keuvviBxvP3/Q5l8Z9cbR99Nlr5i556AM3pB//1ukE5r6v0vTXb/z4UOaJM59s2DM2+JHVxNs1OvC3X/ryT7offm"
         "nx+Zev/fIF0PkdE9+fKh2/5sqRm4/PPJfaWYEuh1/5dGnTM52X3vfdi25+6JsvBMA79cInjszu/odLHvjI/M+3/nP8Naz7eOvXv//t4iPb7v6"
         "rh/7j9j+fOgw7137liZeC337x/V/52QtPf3HP9OsriXfs38+8/ONn923b88h//sWN3c/+I+S96/hzr0R+9rXLi1/45tONT2yccoj3yRW5XxYD"
         "x9//hav67919+dPxMPFeK776y2vOPXxV8amVt36m2nNlLfGO7h75r3t/9I3MeEPzg5+e2f1BzE3YxfVecMgCmsiQ1RfoW18KA5eahPZR+P44f"
         "95EMFRjRkiQybSU5oGzNeYvPcunM06+qTTvWengcLO3aOyk1bfem8b3XKs355HcQkt6xrOKgeL6dGzIWbJoftZzsua2tWbEcxL2bE36DmOKgR"
         "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"
         "37FmxF4IgAA")
    test_slab = ("H4sIAAAAAAACA42cfXRV1ZXAr/CUtyRqhBQykBIqURhJlVUyQCVj7r2JBgkoUzqWWQrGaqUdmPEVUo0kQ5IXk5Dv5IXkJXyYILCC"
                 "5SOx2CZiaDJSBOsM0AU2TIdCtDoB66xkii2ppXXOefec+3X23tR/Su+Pvc/e++y9zzn33cOpz0/94iYtWSuftSnyy2e3mYfzw/03"
                 "33vb2aCmab9NTt6a/eGrS7YveHLzpb0LvjfjJk17K+dsc2T73KySuvRdifekvHQz+3sVrXe3vr3ynLH3saf1nxwYncllF1+YtvO3"
                 "v3ljWc/V56aGd4SeiGPPnmxdf7C69ndZ+9//33cvPl47bwp7du+e010Dx1c+0rLh+Kl3Fn3zAhtC6730/EBKf5rZduKBDXt/+N44"
                 "/mz4ve/8+5l1/2m0P/GrPz70UfLHAfbsJzNeOX2o70fZddG914pe7Oodx57d2tjz/i2Hzi5t/MN7RyvCb33Cx/3Z/129+Ju3a7LD"
                 "P/pzwdqst/+L67vv+DuXJv9h28N9ZT88mtgzq2s8e/bcxPy/9I07vrTs0dzmdQ8fTb6VPfu478O/rLy+/9G+I7dt2ng55xH+7Ni6"
                 "li+af/3aslenJu16/tS6b3Bb4l89dtOftrZn1WS3PfirB79/D39W9D8Txh1Zd/jR3Znf7P/q8r87y8eN+1P45jPt/5i5fSwcP/vT"
                 "E8u5za+sHZukPf3q8t1Hd19/9+79825jz86tuZ7wZuaknOKnn9w9LS/AQ68t+CBjzrFpd+tv9jc8nfrwsm9MZM+mvnvfV7+862+X"
                 "t7304befveWpn3N9t/3izq/PTZj/WPsnqx+IP76wpJY9e+313399yjOTlzf8clLHkXeP1X3Ans39jpH90Kw9j/z0/QeKjlyZvnkh"
                 "e/Z5+PF/MDPPP1Ty68Nf/vzujxtuYc9umfzHlT/92uRlxZu+9/jv7vzv43zeXv7K7d+ufPbOrPI373rg2Kp3crh9yeO+tvZvfv+J"
                 "2XnT7R9mdxf+6xz27O9/fOy7//Sldx7aHXfxXxZ+60s/4H9P07aamlb8IPuDwf5Xt/5crAc9rJhg/D8/e1kw3cTlBiidhBylc6bC"
                 "+q41m72Drxmrh7NNbeTPGdq1TRn64EsZWoxFGTvMWA7AahnbBcodutrIWJeRP8IYf8YY/ztxttx+RK4+Np5fLmDb+RaTy/TIBWNy"
                 "nPUj41UwthPxj7MmRafFmhirZ2w8YGcbYxVsvInKeIeucv+ijE0AbOH+1TKdEwCdzaDOgB3PZnC8vmuVjLUznRMBnaUx32GdJYLd"
                 "gejcqfhuxZrHrBqRKxPxnADIVQofJgO2VDPWyNj9SDzbGVsI5ASP5242XgYwXmOM5Y9kIvPA7ZyLyG1HbGmK5bzfljhPHWUA88Dr"
                 "6CCTywB84KyTyc1XbLFysF2x06mx/YgtVv2tHl4M5DW3s42xhYjv9UxnMmBnk4jZVECulpCz6mH18GTEllqFBe2YNTGd05GYbWdy"
                 "s4C4VIv8hGxpFD7MRmp6L5ObC8SzVMRsMlJj1aCdVo3xmp4N2FIt+st0pFZ2IflSLWyZD8SzUsQTymvZCzKRum1D6qhUzG0G0ltr"
                 "lTxz+gSfv/lAHVWLuIwHWCPBKswP1kT1oaOPGZwFXXHJHykQOZED1FGJyEGKqWtA/siLsZ7l761c7snhAtGz7lDmKH+kSMSTkoPW"
                 "hxIhp645llwl2HctO+E6smyB84zHbGhNj37k1LARs91j50bGrumjF9sN/3jclqE1/TYLeGwpirEjp9o9OjXhX6hrvCGZ17+NQmfU"
                 "ozMg/LPkoqBcqGuq4bczEGNcLpuxTgOKmWXnsGKnpfNFJnfJgGNdwmwZNNT64/6tVVjQjlmPLvM64KnpEjEPXyi2WPHkbARgLwp2"
                 "CZk/Hs/TyhxZ/q01JNMUNpexHiRmfLwuIGYW84/nzN9sFpdOIC58vPvZeF2ILZmM9QO2FDD2Laaz34BqxfJv0IBqjOeL3xZLrkj4"
                 "0GXgc9SjxNqZoxNAXAqEzn5Fp2VnphJr2UNCXfNBOy2WY8jxvKwAzM+gZ46+AOrWslPu3QKAnOw9/lzqHSwF93UyZquH7zDVmBXE"
                 "agzah8g8k+tYQOkT3Jb5gC3SzgxTjTXPwSJwTZXz5x/PW7fqeI5/8xU5hy0GdBYRdvK5LWB2LgbjyWMN7etkP5NrOFSb+SOzTKg2"
                 "LTunmlB/6R0sU9YOza7pdYwlA2sVZxuVPVGcqy/J/ZnaJ4rAPaaV80XIeDKeU8F4WgwaT857NhIzbmc2kGcFYi81HliLi2J7dtnL"
                 "1b1GrSH7td8Hvl8avTgCrGMbxdlpPJC7BTE5uT7454GPN3pxGNFZDzJr3rnOa2C/tvaDmSbUk/keBdpHWjFrAuUOXS2Lre/+dVru"
                 "d3mfgPoZ3ydb/ewa0K8rmdxTSqyD9r61DPSPM15/cl+g7vVLwH0B9wHrrdwWaA2X42F7MD6epXMY8E/KDQJyFYSdMmYnFJ2c8ZhB"
                 "6601D8+Aa44ll63IyTOQNd6gEhcrZv3Ielsp9medYMxCXYsNuRZ7c6IM9M87Dz3KOs1jHerKAPc9/PwX6loJ7jUsuaeUvVTAtnMj"
                 "KMfPXENrTiD+VYv9bieQn7VMbsTeg/nfF1h7ImiOmsVe4wSQE5wlIywqGOQfl5uIxKVNnB/6AZ31MTn/nk++L7D2Z10G9M6R7xWh"
                 "eefvdPj8+X2X7zX4/hPKTytmdyg6NfG+x/IBygnOBpW9sHwfgtUYjxm2V+R2QntF+c4K239asT5h2+mVi4o6guSaRf31AHY2gvWn"
                 "2f6pdevky2Jl7+3kC5+/08gc5YB7ditfnkFYFOwvAc88DAJxaQL7p2bHDO7XVk5wnSNIrLncNSBmzej5z7FzBJiHevBsGBTvUUJd"
                 "z4N7BqseCpB9CI/1E8gZNhrrE9C6yfOMy/n3DHH23K5D1s2osPMakhNFoJ3WO8BS5F1Qfawn+32Ps2s6B9xn8fnjPdJvi3zXbO1b"
                 "x5vQ+gedZTQPm2hCazF2dpLrkXzf482XMkIuKvbCE01ojiy5CaZam00ok33J74P8XQaSC7h6ljz/BZR34mXg+yxZK/6zk+aqaXkG"
                 "8o4n/csE/KsFmdPPepTzUdATl8VEXOYC896Inv+cmC0k5v1+QK4MPG8GPHILAVsqQf+8ubTYhPdgWDxLY/Pnf4cbcO0joTOXUw/J"
                 "Jranle/ZA773uxAL2Hv2UvD8x32w+gT0W0GZsGU6EDPJZhFzO52Y22S0l8t3/nD9zTaxfYHflqCnHqYDcrKOJgM+1As2G8iJNnQe"
                 "HJ05wHuNJsEyTWz/4j8ze3Mix4TPKxXgHtPKwaghz1X+ubXO0yPgOcD6/W888rtMFFwDrDxrVNYjzbazGVzHNO0FU9M+0jWtwWD/"
                 "h/99/hu7j7V6WFyMbWDsDca2AKxQsK38WwDBtIygLXdAt7498I1XvIWxfYytZ0zPEN8FWDqLSxnrYCzNwyy5CsZ6GUv1MOsThhrG"
                 "Whm7rLuZZctG07Lj54DOYjHeSUCuSNg5pqvjFQuWZahy3IfD7PnDpuX7zAwRA/ZftWDjPMyahyh7dpSxBR4WZ7ODjM3wMGu8EqFz"
                 "CiJXzdinhsqaGKtgzy8Yqs5axvqYf926aief291MZhIwHmc/YzJzDNX3Rsb+mT3vA2zh493Hnu9BbGlgOhcJFvvGRNhSLebdyzQP"
                 "m+NhcXbM+LznDqisFGROXmNskxhvoF9lvMYKmR33mbBOnp/TCDYDYVznXQCrFXbuMFRWKXIXYmWixiDG668bYW2CHQDYdoLx/Pwu"
                 "e34OmCPO1rvy089C7PlHCMsldD6L6GwT83dG5Lzmyl0eF96TbB8yvDnI+8dMj1zQzvkh9jzRUHW2iVh7xwvYucT76r2mm8XZOgOG"
                 "o1P3yb3iktNd41WxZzWMDYl+3RHzw7KzlbEtvM95mOZ8nyV6uZ/ViNrMBVihmL+TwHhh0/J7i4dZ/jWYlh29AOO28G/dugGddYzl"
                 "KeNZcdlmWmtDN+ID920MGC/CWL7Cgva8f+qa91zXvFeLGsNyogPJCT5/Lyvz7uTLLsZuBfour82djN0DrDn17FmUsetAb60XOq8D"
                 "/ZrnfKeydjhr3AXmwxIDXuPOufqge+3gdi5V+rzjwwKFBezxNrDnb6isuFbsNdINUc8P2t82xtgOxkIDbmbJ8XhuZWyoX5GLrf18"
                 "b9NiKHIxxseLAOzfBKsD2PeFLQGAFQi59aoP2g8Y26P4ELR94GwboJPXnyniyXN3wNV3+f5lhmH1cj/jtTmNYEtFH3SYZWe56C8p"
                 "psWKXXtMznhMZgKM96UGRE6yJIBtF/16n6uXy5rOE/Un+4tbjrPYXtej06mxV1w1NpDhXf+2uWpswJW79aJfyzoacOUur6M9rjoa"
                 "8O35BnT5zMtKRY9cYqjjyTVH1tiAq/5eEH1wDyDH9ww8Xp8BtmwWcTkHsEphS42hjsfjMk8ZT7N9WO+q2wFfn+hV9mea3a/5WMvk"
                 "HLn6Lmc7CHaAYKM6zhIJuUUEW0WwfIJ1E7bkEozHEGKNIpewdaUG2U+0iLyOB2qMM94DgwCLCLk4gNWJOoJ0NgiWCrCtBGsQ480h"
                 "2ExEZwfSX+R4CYTORCQuHUhfigidSch4OxBbeG8NM5bmYc7ehu/P5nn6mbNHwVgLwbaJfR3FVhAsBLAqsR+0cxNguq6yMCFX/lcw"
                 "SifEZDwhFiFYC8FkXCA7JcNswfyTtkCshWBVYo8ZT8zRkA4zrrNDh2PdiugsJ3RK1kHMEaQzTOgMEzrLhe/zCDtXIOO1Ikz6HiLk"
                 "QoQP85B52EcwzM4qYrw6Yv4kGyJYPNFfOohaGSJYPNGXOogaGyJYPNGXOojaHCIYpLOGyE9pS4hgK5B4YnMre0GIkAsRciuontxP"
                 "9OQBPOcxhukM34BhOusIuTrCzgjBWv4KOWi8bYTcNtl3+4meDLBCUe+tBsw6lPNKnH1ewdaxPBFPaA0oJNaVwhvoxHprHtGT84ha"
                 "KRR2QnKFN5CjbMH6dZ6IZ4iI5zxiHkKEDysIO+cZxBz14wzKs8IbsAZCZ76yhw7ajL/rSgfOvnnifXIawAqFHMYKifHykf2ulEsB"
                 "5GSNbUF6XSvCIoK1EnKthNwWA+8hGMN0biNYFTGe3Lu1IvsJrE+U34DtI3TuI3zoEO9YIN8xVkewCMG2ivcFZwDWINgYwS4jOkMI"
                 "axDsPCKXh7CwqAco5yVLQc5x/Bz+qOv8Lt8vRQjWcgO2g9CJsTqCtYj3RF6m2e/duC1ZpvNbiIzLdqETYwcQVkXYUkX4HibkygkW"
                 "JnSWE0z6kEb4jrEa0XcxuXQiZumETmq8VGK8VEIuhWBJBEtAGH9nNc/A2QqChRCm67hOXcd16jquk4/XoeNsiGDxxHiYTl3Hdeo6"
                 "rnPAVZMQ0wmdmJyu43IxnQOELf3EeAjL1WGdhUTdFhK1mXcDtoNg3AeMcTsx1k2wUYIlErYsItgqguUTMaPYKoItIlgiwTDfC4mY"
                 "FRKxLiTmSOZSK1IrK1zfL0G520owTE7+JgyxVWKvAbFFYj+ByY0RchTDxkskxkskdCYSOvncjhGMksNs6SZ0dhM6uxGdFSKeAx5m"
                 "nTv492dzXL9h+vc2fN73ETnRS7CTBt7r9hGsl2AnCd8p1kvMw0li3iHG34OlKDELenw/T8TlMsHGCN/PE+wywcaIuo0zcRYw8dqM"
                 "Ixgmt4iQW0TIJRJyiYQcn9s4gmFy3YRcNyGXS8jlEnJ83ilGzVE6wdIIlkrMXzrB0giWSsxtOsHSCJZKzHs6wdIIlkrkRDrB0giW"
                 "SuRLOsHSCJZK5FI6wdIIlkrkWTrB0ghG6aTOQEkESyF8SCBYEsFSiFgnECyJYClETiQQLIlgKUTuJhAsiWApRI0lECyJYClEL0gg"
                 "WBLBUoielUCwJIJROrMIW7II3yHWQpwtIgSrI1gLcSaJEKyOYC3EWSZCsDqCtRBnoAjB6gjWQpydIgSrI1gLceaKEKyOYC3EWS1C"
                 "sDqCtRBnvAjB6m5wNkwk8prHLIvodVlEb80iejnEyomcDxOsnMjrMMHKidwNE6ycyM8wwcqJHAwTrJzIszDByolcChOsnMiXMMGq"
                 "iDmqIuahioh1FRHPKiJmVURcqgjfqwj/Gs2xz95jtiy1crd9s+d777HPjjp3mjysWrBxHibvVIx9tt/5nlZhPQirFux2gJUxdkxh"
                 "AZu9ibBqwR4EfIgydsK5e+WRq2Wsy7lfJZhmx6zHuYPjsZOzgwiLCrkZgM4Kxjqd74wVdhhhJWIepgA+8PGanW+QPaxe2HndUO1s"
                 "YqzRuS/jGY/nRL3zba8yD68r4wVtdhRh9ebQ2Uu6dSdIZaNXxhswq2Vyw859Nd88DJ09oTD5jbWlcwno3+iV6QgrEeOJ75l9uTR0"
                 "9guFyXgOnR3Urfr029Ik5CDGdZ527p15bKlmdk417G/BfTkvbAHYJlGbpgmzHys1HRTfiVv5OQOQ2yByaRLANouYaRmQTovN1CEm"
                 "/APkNhHzsFnMLSY36Ny98vkwdHbE+S4d9P0cUCsvMFbpfAevxKXH+e7eI1fJ7Jxg2N/WK323FKmxCib3jDKerIfRK5kKkz1r9EqR"
                 "cw/Tl2ea9h+u+wjuOzj8XsEm5O7OZnnnJ0O9D8TZdte9Av9d0v2u+wgzfXcOLrjuHLh11vi+t9F97yo7XN/p6K5v5LeIb+RzEca/"
                 "yZjpYdZ4+b77JLrrfXKx71sO3fdbFtfXAeiUd4/lt01uluf7xhOSCwE+5Im7GNB4YXHfohWQaxH+QXIN0k7A9wjouyPH90ujgFyL"
                 "+LZiCJBrFfc3zwNM7rO6ER/c347ovjuFeQoL2OPtc32P4rczVfyOUOzbz/P7Fsec/ZJyP+6gcgfcubtzULkD7tw/iiJ3/Lhcl7O3"
                 "8bAyofN24F45l3vd2fd47OT13qPcOXfuEHcq98qdu9y7XHeP/XfOO5W76s79vybknmKJ8GEKYmcZcheR372qVe4wOnevdiJyUXHn"
                 "Tt7l9t9hPIDcYdwk7r+bJszUuQ3afbAdicsGYeckRO4A0ls3iXuKZ5B7+geUu/hxdi9/jujljUS/3oX06yZxFzFXh/9tgz3IulIq"
                 "fFiC/JsBe5B/h6AWZM6d1wPOPtITz0oxHrSucB9KlH8Twcndu5SYOffc1sD3U2N23oXca20Ucn2AnbwXnFfuh8tz3OiVlaIvxRvW"
                 "n4eM/weiPmO1hGYAAA==")
    test_slab_v2 = \
        "H4sIAAAAAAAACjv369xFJgZGBgYGgUWHGX9Pme/S4z7T7pZdoRonUGwCSIKhgRFMS0L4DTwMDCcYwOIsDBDADOZLQsRB8gxQPgOcDwD7jJ0vaAAAAA=="
    test_slab_v3 = (
        "H4sIAAAAAAAAC71YMWsUURCe927VFVZYYQkGrgyieI1kQbS4ywVBEESwFcGfoGKftRQttrDQKsFfcEW6S8iB2IakTZXGxiYiCEGLc/ftHftmb"
        "mYutwYPjmzyMfNmvm9m3mz2f+8fGrAQf/5i/nzYvP/+wafuUffl9bfw8MWVw6t3byWrjze/P7sXf73z5mbxN4D2OkDWBRj0i5+96jnrRS0oPi"
        "sTLEdYaH1sC2GBw6Y+R4xdx2GG2PkYtYuQTxwLuE/C2gXgxzlg7NpsDqHLPT0DRs5DGD4vBB/LGa4Tns+WH+cCGiFM83lOGiE+iUZW0QjV0oC"
        "xEzSyikZW0cgqGllFI6to5LBI6ZWI1w9hIyb3gD2vqt2IjwV8u4Gi0YHSKwdKj3F2qWLXUeyEGkR2XJ1p/S7o/vrkpOaFi1PQYXl5V+y/b++G"
        "tc9M1MHAc4yZEjvtV7+vMXYVRu0i8O3weeF4PK5jwT4BnUd4Gb76WWOcRhJn2Y3ajvSfdt5OeZ5Qn8gu7/8Yb9RY/nRL7Afjx0l0+LV3LOqAd"
        "MechSj3NbFeZjRycSasnV+71M6vecPatRWfKYvhfsiYHDoz2GnBeaVDdZ5la7CyaxEMvBnC59dmY6nqJZH6aLsRn64fBD6Nwqfrh0Z8po34dP"
        "0g8Vl+JT7L5wZ83u49EWcd6jFuRgqzde5MFmf5tnwHlM/a3SHcOSj3Re847W7UZtZZ7mLtDic6uNoVdgZ0Htk1XO0KOwriLKc6gLgTGUX3Hb9"
        "XyB2A+OQwYedD+o2Y2tXeA7SdQdhpUZykBt3dIezQKIdc8cntYIJGrv8aaDS3N89ZI63f0Wz9DxoZP85FNUp4jS7HWY2RHMISm8ZJfF6qsRmf"
        "Dlvhc7hYYgF7XnDBxwhngeLTYdM5gedZ1FJ8WsWnUfIzMYi8gMKnjWUdNI0QRnwakGPxsBmfj8r/hwi5o1meM3Um8IlqkPMpaPRPPoX8QOHFv"
        "ecIfM7VQYjTzevpPs/NLMFuY+lY5Br1e6bwQvb53eFqzTXd3cpvyu5ngO4A7h1BjGVP9On2nmsTu48FBhOOoP8Xj6O7dcATAAA=")
    test_slab_v4 = "H4sIAAAAAAAACj2UsWsVQRDG53nGRN0i2F0XhNNX3x9wKAoWh6WskMZi/4C1s1l5pDtIISKHYhF4WNjFShQRBAtThWcb/AMsLCzFNO7M/PCaYXZ2v++b73b29O/p9wvSiMju+uvi/MXR3cN7r4az4fENWYiE84OtzdGDO6//HOze/PXtfl2Sj/vv97+8Pbt9+ObH5+vPrz3VtQ9XT2T1SZrfVzSuFprLsYjmNTZWX1Nfey4z9dn3r6bVwuoT9eK5FPAz5zP4iXoCP1KP1EfqI+cH8Afwe99fo9c711Oj11vOt9QD+AF8QX/9lvT96LLHlzvmh2y23ZedbV+/dcnzJ1tef3fR15f4pOfl2M9r1PPq447HRs/rup7XqOe1vnRfxfhrNP7qs/Gv4a/rxl+j8a/9vOZL/oPxz17Xz/Dr97NxnXuN6394weOzha+fiPcj4rnuV717jevU/apT9+u67tdcPDaGX3UY/tr3a274a93lfYhH06M69zyaHs0Nf3Y9mhv+7Hr0fhn+JGL4NTf8Cf0T+ifwC/oL+gv4xfXouhANP4Of0Z/Rn8HP4Gf8SehP4CfXo+uGn7xfjYYf8SeiP+J/BD/iT0T/iP7R92s0/BF/RvwZwR98v86J4Q/oH/B/8H41N/we/B78Hv09+D34Pfgd+B36O/A7vw+rDvwOf1r3U+fP8Fv0t/jT4k8LfgA/cD8D+AF/Av4H318/1y/cH0G/cD8F/eJzq+s2h+Jzres2p8LcCHNc99lcBeYsMHeBOQw+17pucxqY28AcB+a6Zc5bP699Gn/rc63rxt/C3zLHLfwd/B381Vfj73gXOt6pjnerc/263/h73oGe/nv4e/rv6b93/Vpf8p4a/+D6NRr/4O+Yxg3R+Af6H+h/cP16L41/5N0bXb/mG4/e/0j/I/2PvGsR/kj/Ef8j/DU3/kj/kf4j/Sf4E/4n3uHEu5zoP/FuJ/5/gj/jf6b/jP8Z/zP9Z/gz/Wf6L/AX+Av9F/ov8Bf8L/Rf+P8T/BP9T/BP3L8J/sn1azT+ifs3wz/z/2f4Z/qf8X+W/1+1qHLpHP8Dolb431gIAAA="
    slab = TSSlab()
    slab.decode_slab(test_slab_v02)
    # pprint(slab.data)
    # remaining = len(slab._binary_data) - slab._offset
    # print(f"Remaining Bytes: {remaining}")
    # print(slab._unpack_utf8(remaining))
    new_slab = TSSlab()
    new_slab.data = slab.data
    encoded_slab = new_slab.encode_slab(force_version=2)
    pprint(new_slab.data.keys())
    pyperclip.copy(encoded_slab)


