from fit_tool.definition_message import DefinitionMessage
from fit_tool.fit_file import FitFile
from fit_tool.fit_file_builder import FitFileBuilder
from fit_tool.profile.messages.device_info_message import DeviceInfoMessage
from fit_tool.profile.messages.file_creator_message import FileCreatorMessage
from fit_tool.profile.messages.file_id_message import FileIdMessage
from fit_tool.profile.profile_type import GarminProduct, Manufacturer
from typing import IO
from datetime import datetime
from io import BytesIO

def rewrite_file_id_message(
        m: FileIdMessage,
        message_num: int,
    ) -> tuple[DefinitionMessage, FileIdMessage]:
    dt = datetime.fromtimestamp(m.time_created / 1000.0)  # type: ignore
    new_m = FileIdMessage()
    new_m.time_created = (
        m.time_created if m.time_created 
        else int(dt.now().timestamp() * 1000)
    )
    if m.type:
        new_m.type = m.type
    if m.serial_number is not None:
        new_m.serial_number = m.serial_number
    if m.product_name:
        # garmin does not appear to define product_name, so don't copy it over
        pass
    
    if (
        m.manufacturer == Manufacturer.DEVELOPMENT.value or 
        m.manufacturer == Manufacturer.ZWIFT.value or 
        m.manufacturer == Manufacturer.WAHOO_FITNESS.value or 
        m.manufacturer == Manufacturer.PEAKSWARE.value
    ):
        new_m.manufacturer = Manufacturer.GARMIN.value
        new_m.product = GarminProduct.EDGE_830.value

    return (DefinitionMessage.from_data_message(new_m), new_m)

def process(stream: IO[bytes]) -> IO[bytes]:
    original = FitFile.from_bytes(stream.read())
    builder = FitFileBuilder(auto_define=True)
    for i, record in enumerate(original.records):
        message = record.message
        # change file id to indicate file was saved by Edge 830
        if message.global_id == FileIdMessage.ID:
            if isinstance(message, DefinitionMessage):
                # if this is the definition message for the FileIdMessage, skip it
                # since we're going to write a new one
                continue
            if isinstance(message, FileIdMessage):
                # rewrite the FileIdMessage and its definition and add to builder
                def_message, message = rewrite_file_id_message(message, i)
                builder.add(def_message)
                builder.add(message)
                # also add a customized FileCreatorMessage
                message = FileCreatorMessage()
                message.software_version = 975
                message.hardware_version = 255
                builder.add(DefinitionMessage.from_data_message(message))
                builder.add(message)
                continue
        
        if message.global_id == FileCreatorMessage.ID:
            # skip any existing file creator message
            continue

        # change device info messages
        if message.global_id == DeviceInfoMessage.ID:
            if isinstance(message, DeviceInfoMessage):
                if (
                    message.manufacturer == Manufacturer.DEVELOPMENT.value or
                    message.manufacturer == 0 or
                    message.manufacturer == Manufacturer.WAHOO_FITNESS.value or
                    message.manufacturer == Manufacturer.ZWIFT.value or
                    message.manufacturer == Manufacturer.PEAKSWARE.value
                ):
                    message.garmin_product = GarminProduct.EDGE_830.value
                    message.product = GarminProduct.EDGE_830.value  # type: ignore
                    message.manufacturer = Manufacturer.GARMIN.value
                    message.product_name = ""

        builder.add(message)
    modified = builder.build()
    return BytesIO(modified.to_bytes())
