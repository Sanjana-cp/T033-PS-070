from command_processor import CommandProcessor


def test_sample_data_loads_and_allotment_runs(sample_system):
    data = sample_system["data"]
    hostels = sample_system["hostels"]
    students = sample_system["students"]
    engine = sample_system["allotment_engine"]

    assert len(hostels) == 4
    assert sum(len(hostel.rooms) for hostel in hostels.values()) == 304
    assert len(students) == 640
    assert len(engine.allotments) == 640

    assert engine.allotments["STU-0553"].priority_score == 94
    assert engine.allotments["STU-0300"].priority_score == 94
    assert "NO_PREFERENCE_MATCH" in engine.allotments["STU-0377"].flags
    assert "RESERVED_DISABILITY" in engine.allotments["STU-0631"].flags


def test_command_processor_skips_comments_and_keeps_order(tmp_path):
    command_file = tmp_path / "commands.txt"
    command_file.write_text(
        "# comment\n\nFIRST|one\nSECOND|two\n",
        encoding="utf-8",
    )
    processed = []

    processor = CommandProcessor({
        "FIRST": lambda fields: processed.append(("FIRST", fields)),
        "SECOND": lambda fields: processed.append(("SECOND", fields)),
    })
    processor.process_file(command_file)

    assert processed == [
        ("FIRST", ["one"]),
        ("SECOND", ["two"]),
    ]
    assert processor.rejections == []