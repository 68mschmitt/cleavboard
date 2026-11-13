"""Read-only qualification of the rev0.7 controller interface.

Dimensions independently transcribed from Harwin M20-786 issue 10 and Samtec
TSW style 14. Tolerance assumptions are explicit, not vendor approval or a
substitute for a sample insertion/retention/USB test.
"""
import csv
import json
from pathlib import Path

import pcbnew

from design import ROOT, REVISION


def validate_interface(board):
    fps={f.GetReference():f for f in board.GetFootprints()}
    assert not list(fps['U1'].Pads()), 'U1 must not retain direct-solder copper'
    result=[]
    # Independent coordinates: USB-end entry x=449.8975, row y=4.50/22.28.
    for ref,y in [('J1',4.5),('J2',22.28)]:
        fp=fps[ref]
        assert fp.GetLayer()==pcbnew.B_Cu and fp.GetAttributes() & pcbnew.FP_SMD
        assert fp.GetField('MPN').GetText()=='M20-7862042'
        assert fp.GetField('LCSC').GetText()=='C5379059'
        pads={int(p.GetNumber()):p for p in fp.Pads() if p.GetNumber()}
        holes=[p for p in fp.Pads() if p.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH]
        assert set(pads)==set(range(1,21)) and len(holes)==20
        for i in range(1,21):
            x=449.8975-2.54*(i-1)
            pad=pads[i]
            expected_y=y+(-1.7 if i%2 else 1.7)
            actual=pcbnew.ToMM(pad.GetPosition())
            assert abs(actual[0]-x)<1e-6 and abs(actual[1]-expected_y)<1e-6, (ref,i,'stagger/entry error')
            assert pad.GetAttribute()==pcbnew.PAD_ATTRIB_SMD
            assert tuple(pcbnew.ToMM(pad.GetSize()))==(1.02,1.8)
            assert all(pad.IsOnLayer(l) for l in (pcbnew.B_Cu,pcbnew.B_Paste,pcbnew.B_Mask))
            assert not pad.IsOnLayer(pcbnew.F_Cu)
            matching=[h for h in holes if abs(pcbnew.ToMM(h.GetPosition().x)-x)<1e-6
                      and abs(pcbnew.ToMM(h.GetPosition().y)-y)<1e-6]
            assert len(matching)==1, (ref,i,'pin entry hole moved')
            hole=matching[0]
            assert not hole.GetNumber() and hole.GetNetCode()==0
            assert tuple(pcbnew.ToMM(hole.GetDrillSize()))==(1.,1.)
            result.append(dict(socket=ref, socket_pin=i, module_pin=i if ref=='J1' else 41-i,
                               entry_x_mm=round(x,4), entry_y_mm=y,
                               solder_x_mm=round(actual[0],4), solder_y_mm=round(actual[1],4),
                               net=pad.GetNetname()))
    # Depth from socket's PCB-facing entry, with insulators seated on carrier.
    # Female contact is 3.66mm from its far/top entry on the 7.50mm body.
    depth_min=(8.13-.13)-(1.6+.16)-.2
    depth_max=(8.13+.13)-(1.6-.16)
    # Unqualified 7.5 height uses Harwin's GENERAL X.X +/-0.50mm tolerance.
    contact_max=(7.5+.5)-(3.66-.1)
    far_end_min=7.5-.5
    assert depth_min-contact_max>1.5, 'Insufficient bottom-entry contact engagement'
    assert far_end_min-depth_max>.1, 'Male pins project into case backstops'
    return dict(socket_mpn='M20-7862042', socket_quantity=2, lcsc='C5379059',
                mating_header_mpn='TSW-120-14-G-S', mating_header_quantity=2,
                header_orientation='8.13mm gold posts DOWN; solder 2.79mm tails to module only',
                board_thickness_mm=1.6, male_post_length_mm=8.13,
                tolerance_assumptions_mm=dict(male_post=.13, board_thickness=.16,
                                             seating_gap_max=.2, socket_height=.5, contact_position=.1),
                minimum_insertion_from_socket_entry_mm=round(depth_min,4),
                maximum_insertion_from_socket_entry_mm=round(depth_max,4),
                minimum_depth_beyond_contact_point_mm=round(depth_min-contact_max,4),
                minimum_pin_tip_to_socket_far_end_mm=round(far_end_min-depth_max,4),
                module_header_insulator_height_mm=2.54,
                nominal_module_top_envelope_mm=7.64,
                case_checked_module_top_envelope_mm=8.2,
                nominal_socket_height_below_carrier_mm=7.5,
                maximum_socket_height_below_carrier_mm=8.0,
                nominal_npth_to_solder_land_clearance_mm=.3,
                npth_drill_mm=1, required_drill_tolerance_mm=.05,
                maximum_insertion_force_all_40_contacts_N=80,
                preheadered_waveshare_20808_qualified=False,
                physical_mating_tested=False, jlc_order_preview_approved=False,
                supplier_dfm_approved=False, pin_map=result)


def write_outputs(board,out):
    out.mkdir(parents=True,exist_ok=True)
    report=validate_interface(board)
    (out/'controller-interface.json').write_text(json.dumps(report,indent=2)+'\n')
    with (out/'controller-pin-map.csv').open('w',newline='') as file:
        writer=csv.DictWriter(file,fieldnames=list(report['pin_map'][0]),lineterminator='\n')
        writer.writeheader();writer.writerows(report['pin_map'])
    print('PASS: 40 NPTH entries, 40 underside SMT lands, pin mapping and long-post depth budget')


if __name__=='__main__':
    write_outputs(pcbnew.LoadBoard(str(ROOT/'Cleaver.kicad_pcb')),ROOT/f'manufacturing/rev{REVISION}')
