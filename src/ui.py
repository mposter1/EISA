import sys
from copy import copy

from PyQt6.QtCore import Qt, QDir, QEvent
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import *
from PyQt6.uic.properties import QtCore, QtGui

import memory_devices
from memory_subsystem import MemorySubsystem
from pipeline import PipeLine, Instruction, DecodeError, Instructions, OpCode, ConditionCode

from eisa import EISA

# from debug import *
# from main import *

# UI Remaining TODO
# TODO - Implement line edits for rows and columns of memory tables
# TODO - Implement line edits for read and write speeds of memory tables
# TODO - Implement print statements for reads, writes, and each stage -> Reorganize cache + regs tables to be columns
#  with output as a third column

'''
class TableModel(QStandardItemModel):

    def __init__(self):
        super().__init__()

    def setMatrix(self, matrix):

        self.setColumnCount(len(matrix[0]))
        for (i, colHeader) in enumerate(matrix[0]):
            self.setHeaderData(i, Qt.Horizontal, colHeader)

        for (i, row) in enumerate(matrix[1:]):
            self.insertRow(i)
            for (j, cell) in enumerate(row):
                self.setData(self.index(i, j), cell)
'''


def format_list_to_table(rows: int, cols: int, table_list: list[int]) -> list[list]:
    table = []

    for i in range(rows + 1):
        table.append([0 for j in range(cols + 1)])

    list_counter = 0
    for i in range(1, rows + 1):
        for j in range(1, cols + 1):
            table[i][j] = table_list[list_counter]
            list_counter += 1

    return table


def set_headers(rows: int, cols: int, table: list[list]) -> list[list]:
    row_headers = []
    for i in range(rows + 1):
        table[i][0] = f"Base: {cols * (i)}"
        row_headers.append(table[i][0])

    for i in range(cols + 1):
        table[0][i] = f"Offset: {i}"

    return table, row_headers  # TODO - Test whether this returns the correct table


class MemoryGroup:
    ram_table: list[list]
    cache_table: list[list]
    regs_table: list[list]

    ram_rows: int
    ram_cols: int

    cache_rows: int
    cache_cols: int

    regs_rows: int
    regs_cols: int

    memory: MemorySubsystem

    ram_widget: QTableWidget
    cache_widget: QTableWidget
    regs_widget: QTableWidget

    def __init__(self, regs: list[int], memory_subsystem: MemorySubsystem):

        self.ram_cols = 8
        self.ram_rows = int(EISA.ADDRESS_SPACE / self.ram_cols)

        self.cache_rows = 2
        self.cache_cols = 8

        self.regs_rows = 4
        self.regs_cols = 8

        self.ram_box = QGroupBox("Memory")
        ramvbox = QVBoxLayout()

        self.cache_box = QGroupBox("Cache")
        cachevbox = QVBoxLayout()

        self.regs_box = QGroupBox("Registers")
        regsvbox = QVBoxLayout()

        self.memory = memory_subsystem

        self.ram = self.memory._RAM
        self.cache = self.memory._cache._cache  # NOTE - List of Cacheways
        self.regs = regs

        self.load_memory()

        ramvbox.addWidget(self.ram_widget)
        cachevbox.addWidget(self.cache_widget)
        regsvbox.addWidget(self.regs_widget)

        ramvbox.setSpacing(0)

        self.ram_box.setLayout(ramvbox)
        self.cache_box.setLayout(cachevbox)
        self.regs_box.setLayout(regsvbox)

    def load_ram(self):
        self.ram_table, row_headers = set_headers(self.ram_rows, self.ram_cols,
                                                  format_list_to_table(self.ram_rows, self.ram_cols, self.ram))
        self.ram_widget = QTableWidget(self.ram_rows, self.ram_cols)
        for i in range(1, self.ram_rows + 1):
            for j in range(1, self.ram_cols + 1):
                temp = QTableWidgetItem()
                temp.setData(0, self.ram_table[i][j])
                self.ram_widget.setItem(i - 1, j - 1, temp)

        self.ram_widget.setHorizontalHeaderLabels(self.ram_table[0])
        self.ram_widget.setVerticalHeaderLabels(row_headers)

    def load_cache(self):
        self.cache_table, row_headers = set_headers(self.cache_rows, self.cache_cols,
                                                    format_list_to_table(self.cache_rows, self.cache_cols, self.cache))
        self.cache_widget = QTableWidget(self.cache_rows, self.cache_cols)
        for i in range(1, self.cache_rows + 1):
            for j in range(1, self.cache_cols + 1):
                temp = QTableWidgetItem()
                temp.setData(0, self.cache_table[i][j])
                self.cache_widget.setItem(i - 1, j - 1, temp)

        self.cache_widget.setHorizontalHeaderLabels(self.cache_table[0])
        self.cache_widget.setVerticalHeaderLabels(row_headers)

    def load_regs(self):
        self.regs_table, row_headers = set_headers(self.regs_rows, self.regs_cols,
                                                   format_list_to_table(self.regs_rows, self.regs_cols, self.regs))
        self.regs_widget = QTableWidget(self.regs_rows, self.regs_cols)
        for i in range(1, self.regs_rows + 1):
            for j in range(1, self.regs_cols + 1):
                temp = QTableWidgetItem()
                temp.setData(0, self.regs_table[i][j])
                self.regs_widget.setItem(i - 1, j - 1, temp)

        self.regs_widget.setHorizontalHeaderLabels(self.regs_table[0])
        self.regs_widget.setVerticalHeaderLabels(row_headers)

    def load_memory(self):
        self.load_ram()
        self.load_cache()  # TODO - not loading cache for now. Need Brendon to look at reading cache vals
        self.load_regs()


class StageGroup:
    fields: list[QLabel]

    def __init__(self, stage_name: str):
        self.stage = QGroupBox(stage_name)
        self.fields = []
        vbox = QVBoxLayout()

        '''
        self.encoded = QLabel("Encoded: ERROR")
        vbox.addWidget(self.encoded)

        self.opcode = QLabel("Opcode: ERROR")
        vbox.addWidget(self.opcode)

        self.reg1 = QLabel("Reg 1: ERROR")
        vbox.addWidget(self.reg1)

        self.reg2 = QLabel("Reg 2: ERROR")
        vbox.addWidget(self.reg2)

        self.reg3 = QLabel("Reg 3: ERROR")
        vbox.addWidget(self.reg3)

        self.op1 = QLabel("Op 1: ERROR")
        vbox.addWidget(self.op1)

        self.op2 = QLabel("Op 2: ERROR")
        vbox.addWidget(self.op2)

        self.op3 = QLabel("Op 3: ERROR")
        vbox.addWidget(self.op3)

        self.computed = QLabel("Computed: ERROR")
        vbox.addWidget(self.computed)
        '''
        opcode = QLabel("Opcode: Null")
        self.fields.append(opcode)
        vbox.addWidget(opcode)

        computed = QLabel("Computed: Null")
        self.fields.append(computed)
        vbox.addWidget(computed)

        for i in range(2, EISA.MAX_INSTRUCTION_FIELDS):
            self.fields.append(QLabel(""))
            vbox.addWidget(self.fields[i])

        stalled = QLabel("")
        self.fields.append(stalled)
        vbox.addWidget(stalled)

        self.stage.setLayout(vbox)


class Dialog(QMainWindow):
    """Dialog."""

    _memory: MemorySubsystem
    _pipeline: PipeLine
    _hex: bool

    already_max: bool

    fp: any
    program_lines: list

    def __init__(self, memory: MemorySubsystem, pipeline: PipeLine, parent=None):
        """Initializer."""
        super().__init__(parent)
        self._memory = memory
        self._pipeline = pipeline
        self._hex = True
        self.run_to_completion = False

        self.setWindowTitle('Encryptinator')
        self.dlgLayout = QVBoxLayout()  # QVBoxLayout()
        self.whole_layout = QHBoxLayout()
        self.build_pipeline_layout()

        self.memory_group = MemoryGroup(self._pipeline._registers, self._pipeline._memory)
        self.build_memory_layout()

        self.update_ui()

        self.whole_layout.addLayout(self.dlgLayout)

        self.setLayout(self.whole_layout)

        # self.setMaximumWidth(self.memory_group.ram_box.maximumWidth() + self.memory_group.regs_box.maximumWidth())

        self.main_widget = QWidget()
        self.main_widget.setLayout(self.whole_layout)

        self.setCentralWidget(self.main_widget)

        self.memory_group.ram_widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.memory_group.regs_widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)
        self.memory_group.cache_widget.setSizeAdjustPolicy(QAbstractScrollArea.SizeAdjustPolicy.AdjustToContents)

        self.already_max = False

    def changeEvent(self, a0) -> None:
        if self.isMaximized() and not self.already_max:
            self.memory_group.regs_widget.setMaximumWidth(self.memory_group.regs_widget.width())
            self.memory_group.cache_widget.setMaximumWidth(self.memory_group.cache_widget.width())
            self.already_max = True

        # self.pipeline_group.setMaximumHeight(self.pipeline_group.height())

        # self.already_max = False

        # self.setMaximumHeight(700)#740)
        # self.memory_group.regs_box.maximumHeight() + self.memory_group.cache_box.maximumHeight() + self.pipeline_group.maximumHeight())

    '''
    def build_ui(self):
        app = QApplication(sys.argv)
        # Build UI dialog box
        dlg = Dialog()
        dlg.update_ui()
        dlg.show()
        # sys.exit(app.exec_())
    '''
    '''
    def changeEvent(self, a0):
        try:
            if self.isMaximized() and not self.already_max:
                self.spacer = QSpacerItem(self.memory_group.regs_box.width(),
                                          self.memory_group.ram_box.height() - 700)
                self.dlgLayout.addSpacerItem(self.spacer)
                self.already_max = True
            elif not self.isMaximized():
                temp = self.dlgLayout.takeAt(3)
                del temp
                del self.spacer
                self.already_max = False
        except AttributeError as e:
            pass
    '''

    def closeEvent(self, a0):
        try:
            self.fp.close()
        except AttributeError:
            pass
        a0.accept()

    def update_ui(self):
        self.destroy_stage_fields()
        self.load_stages()
        self.update_memory()
        self.pc_counter.setText(f"PC: {self._pipeline._pc}")
        self.SP.setText(f"Stack Pointer: {str(self._pipeline.sp)}")
        self.cycle_counter.setText(f"Cycles: {self._pipeline._cycles}")
        self.flags.setText(f"Flags: {str(self._pipeline.condition_flags)}")

    def cycle_ui(self, event):
        try:
            cycles = int(self.cycles_editor.text())
        except ValueError:
            self.error_dialog = QMessageBox().critical(self, "Invalid Cycle Number",
                                                       "Please enter a valid number of cycles.")
            return

        if self.run_to_completion:
            while self._pipeline._pipeline[4].opcode != 32:
                self._pipeline.cycle_pipeline()
                if self._pipeline._cycles >= EISA.PROGRAM_MAX_CYCLE_LIMIT:
                    self.error_dialog = QMessageBox().critical(self, "Cycle Limit Reached",
                                                               "Maximum number of cycles reached.")
                    break
            self._pipeline.cycle_pipeline()
        else:
            self._pipeline.cycle(cycles)

        self.update_ui()
        # For later if we want output
        '''
        for i in range(cycles):
            self._pipeline.cycle_pipeline()
            self.update_ui()
        '''

    '''
    def build_cycle_button(self):
        self.cycle_button = QPushButton("Cycle")
        self.cycle_button.clicked.connect(self.cycle_ui)
        self.dlgLayout.addWidget(self.cycle_button, 2, 5)
    '''

    def build_stages(self):
        self.stage_fetch = StageGroup("Fetch")  # self.create_stage_group("Fetch")
        self.stage_decode = StageGroup("Decode")  # self.create_stage_group("Decode")
        self.stage_execute = StageGroup("Execute")  # self.create_stage_group("Execute")
        self.stage_memory = StageGroup("Memory")  # self.create_stage_group("Memory")
        self.stage_writeback = StageGroup("Writeback")  # self.create_stage_group("Writeback")
        self.stages = [self.stage_fetch, self.stage_decode, self.stage_execute, self.stage_memory, self.stage_writeback]
        for i in self.stages:
            i.stage.adjustSize()
            i.stage.setMaximumWidth(i.stage.width() + 20)
            i.stage.setMinimumWidth(i.stage.width() + 20)

    def build_pipeline_layout(self):

        self.build_stages()

        stages_layout = QHBoxLayout()  # QGridLayout()
        stages_layout.addWidget(self.stage_fetch.stage)
        stages_layout.addWidget(self.stage_decode.stage)
        stages_layout.addWidget(self.stage_execute.stage)
        stages_layout.addWidget(self.stage_memory.stage)
        stages_layout.addWidget(self.stage_writeback.stage)

        self.reload_button = QPushButton("Reload Program")
        self.reload_button.clicked.connect(self.reload_program)
        self.load_button = QPushButton("Load Program")
        self.load_button.clicked.connect(self.load_program_from_file)
        self.exch_button = QPushButton("Load Exch. Sort")
        # self.exch_button.clicked.connect(self.load_exchange_demo)  # TODO - Implement Exchange Sort Benchmark/Demo
        self.matrix_button = QPushButton("Load Matrix Mult.")
        self.matrix_button.clicked.connect(self.load_matrix_demo)  # TODO - Implement Matrix Multiply Benchmark/Demo
        self.cycle_button = QPushButton("Cycle")
        self.cycle_button.clicked.connect(self.cycle_ui)

        button_layout = QHBoxLayout()
        button_layout.addWidget(self.reload_button)
        button_layout.addWidget(self.load_button)
        button_layout.addWidget(self.exch_button)
        button_layout.addWidget(self.matrix_button)
        button_layout.addWidget(self.cycle_button)

        counters_group = QGroupBox()
        counters_layout = QHBoxLayout()

        self.pc_counter = QLabel(f"PC: {self._pipeline._pc}")
        self.SP = QLabel(f"Stack Pointer: {self._pipeline.sp}")
        self.flags = QLabel(f"Flags: {str(self._pipeline.condition_flags)}")
        self.cycle_counter = QLabel(f"Cycle: {self._pipeline._cycles}")

        counters_layout.addWidget(self.pc_counter, alignment=Qt.Alignment.AlignLeft)  # TODO - Add LR and ALU regs
        counters_layout.addWidget(self.SP, alignment=Qt.Alignment.AlignLeft)
        counters_layout.addWidget(self.cycle_counter, alignment=Qt.Alignment.AlignLeft)
        counters_layout.addWidget(self.flags, alignment=Qt.Alignment.AlignLeft)
        counters_group.setLayout(counters_layout)
        # counters_group.setMaximumHeight(self.pc_counter.fontMetrics().height() + 20)

        options_group = QGroupBox("Options")
        self.options_group = options_group
        options_layout = QVBoxLayout()

        self.pipeline_enabled = QCheckBox("Disable Pipeline")
        self.pipeline_enabled.toggled.connect(self.toggle_pipeline)

        self.cache_enabled_box = QCheckBox("Disable Cache")
        self.cache_enabled_box.toggled.connect(self.toggle_cache)  # TODO - implement toggle cache

        cycle_layout = QVBoxLayout()
        self.multi_cycle_enabled_box = QCheckBox("Enable Multi-Cycle")
        self.multi_cycle_enabled_box.toggled.connect(self.enable_multi_cycle)
        cycle_layout.addWidget(self.multi_cycle_enabled_box)
        minor_cycle_layout = QHBoxLayout()
        self.cycles_editor = QLineEdit("1")
        minor_cycle_layout.addWidget(QLabel("Cycles: "))
        minor_cycle_layout.addWidget(self.cycles_editor)
        cycle_layout.addLayout(minor_cycle_layout)
        self.cycles_editor.setDisabled(True)

        self.run_to_completion_enabled_box = QCheckBox("Enable Run-To-Completion")
        self.run_to_completion_enabled_box.toggled.connect(self.toggle_run_to_completion)

        self.hex_button_box = QCheckBox("Hex Toggle")
        self.hex_button_box.toggled.connect(self.hex_toggle)

        options_layout.addWidget(self.pipeline_enabled)
        options_layout.addWidget(self.cache_enabled_box)
        options_layout.addLayout(cycle_layout)
        options_layout.addWidget(self.run_to_completion_enabled_box)
        options_layout.addWidget(self.hex_button_box)

        options_group.setLayout(options_layout)

        pipeline_group = QGroupBox("Pipeline")

        pipeline_layout = QVBoxLayout()
        pipeline_layout.addWidget(counters_group)
        pipeline_layout.addLayout(stages_layout)
        pipeline_layout.addLayout(button_layout)

        pipeline_group.setLayout(pipeline_layout)

        self.pipeline_group = pipeline_group

        self.pipeline_options_layout = QHBoxLayout()
        self.pipeline_options_layout.addWidget(self.pipeline_group)
        self.pipeline_options_layout.addWidget(options_group)

        pipeline_width = 0

        for i in self.stages:
            pipeline_width += i.stage.width() + 20

        pipeline_group.setMaximumWidth(pipeline_group.width() + 40)
        # pipeline_group.setMaximumHeight(pipeline_group.height())

        self.dlgLayout.addLayout(self.pipeline_options_layout)

        self.load_button.setAutoDefault(False)
        self.exch_button.setAutoDefault(False)
        self.matrix_button.setAutoDefault(False)

    def toggle_run_to_completion(self):
        self.run_to_completion = not self.run_to_completion

    def enable_multi_cycle(self):
        self.cycles_editor.setText("1")
        if self.cycles_editor.isEnabled():
            self.cycles_editor.setDisabled(True)
        else:
            self.cycles_editor.setDisabled(False)

    def toggle_cache(self):
        self._memory.cache_enabled = not self._memory.cache_enabled
        if self._memory.cache_enabled:
            self._memory._cache = memory_devices.Cache(self._memory.cache_size_original, 2, self._memory._RAM,
                                                       self._memory.cache_read_speed, self._memory.cache_write_speed,
                                                       self._memory.cache_evict_cb)
        else:
            self._memory._cache = memory_devices.Cache(0, 0, self._memory._RAM, self._memory.cache_read_speed,
                                                       self._memory.cache_write_speed, self._memory.cache_evict_cb)
        self.update_ui()

    def toggle_pipeline(self):
        self._pipeline.yes_pipe = not self._pipeline.yes_pipe

    def resize_tables(self):

        # Max tables width

        # halve_width_size = 884
        ram_width = ((self.memory_group.ram_widget.columnWidth(
            0) * self.memory_group.ram_widget.columnCount()) + self.memory_group.ram_widget.verticalScrollBar().width()) + 27  # 1022
        regs_width = ((self.memory_group.regs_widget.columnWidth(
            0) * self.memory_group.regs_widget.columnCount()) + self.memory_group.regs_widget.verticalScrollBar().width())  # 184
        cache_width = ((self.memory_group.cache_widget.columnWidth(
            0) * self.memory_group.cache_widget.columnCount()) + self.memory_group.cache_widget.verticalScrollBar().width())

        # self.memory_group.ram_box.setMaximumWidth(ram_width)
        # self.memory_group.regs_box.setMaximumWidth(regs_width)
        # self.memory_group.cache_box.setMaximumWidth(cache_width)

        # Max tables height

        ram_height = (self.memory_group.ram_widget.horizontalHeader().height() + (
                self.memory_group.ram_widget.rowHeight(0) * (
                self.memory_group.ram_widget.rowCount() + 1)) + self.memory_group.ram_widget.horizontalScrollBar().height())  # 1022
        regs_height = (self.memory_group.regs_widget.horizontalHeader().height() + (
                self.memory_group.regs_widget.rowHeight(0) * (
                self.memory_group.regs_widget.rowCount() + 1)) + self.memory_group.regs_widget.horizontalScrollBar().height())  # 184
        cache_height = (self.memory_group.cache_widget.horizontalHeader().height() + (
                self.memory_group.cache_widget.rowHeight(0) * (
                self.memory_group.cache_widget.rowCount() + 1)) + self.memory_group.cache_widget.horizontalScrollBar().height())  # 122

        # self.memory_group.cache_widget.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # self.memory_group.ram_box.setMaximumHeight(ram_height)
        # self.memory_group.regs_box.setMaximumHeight(regs_height)
        # self.memory_group.cache_box.setMaximumHeight(cache_height)

    def build_memory_layout(self):

        ram_button_layout = QGridLayout()
        self.reset_ram_button = QPushButton("Reset RAM")
        self.reset_ram_button.clicked.connect(self.reset_ram)
        self.reset_ram_button.setAutoDefault(False)
        ram_button_layout.addWidget(self.reset_ram_button, 1, 3, alignment=Qt.Alignment.AlignRight)

        final_ram_layout = self.memory_group.ram_box.layout()
        final_ram_layout.addLayout(ram_button_layout)

        self.whole_layout.addWidget(self.memory_group.ram_box)

        regs_button_layout = QGridLayout()
        self.reset_regs_button = QPushButton("Reset Registers")
        self.reset_regs_button.clicked.connect(self.reset_regs)
        self.reset_regs_button.setAutoDefault(False)
        regs_button_layout.addWidget(self.reset_regs_button, 1, 3, alignment=Qt.Alignment.AlignRight)

        final_regs_layout = self.memory_group.regs_box.layout()
        final_regs_layout.addLayout(regs_button_layout)

        self.dlgLayout.addWidget(self.memory_group.regs_box)

        cache_button_layout = QGridLayout()
        self.reset_cache_button = QPushButton("Reset Cache")
        self.reset_cache_button.clicked.connect(self.reset_cache)
        self.reset_cache_button.setAutoDefault(False)
        cache_button_layout.addWidget(self.reset_cache_button, 1, 5, alignment=Qt.Alignment.AlignRight)

        final_cache_layout = self.memory_group.cache_box.layout()
        final_cache_layout.addLayout(cache_button_layout)

        self.dlgLayout.addWidget(self.memory_group.cache_box)

        self.dlgLayout.addStretch()

        # self.resize_tables()

        # self.dlgLayout.addSpacerItem(QSpacerItem(self.memory_group.regs_box.width(), self.memory_group.ram_box.height() - 700))

    def reset_ram(self):
        for i in range(EISA.RAM_ADDR_SPACE):
            self._memory._RAM[i] = 0
        self.update_ui()

    def reset_regs(self):
        for i in range(len(self._pipeline._registers)):
            self._pipeline._registers[i] = 0
        self.update_ui()

    def reset_cache(self):
        self._memory._cache = memory_devices.Cache(self._memory.cache_size_original, 2, self._memory._RAM,
                                                   self._memory.cache_read_speed, self._memory.cache_write_speed,
                                                   self._memory.cache_evict_cb)
        self.update_ui()

    def destroy_stage_fields(self):
        for i in self.stages:
            for j in range(EISA.MAX_INSTRUCTION_FIELDS):
                i.fields[j].setText("")

    def load_stage(self, stage: int):
        '''Loads a SINGLE SPECIFIED stage of the pipeline into the UI'''

        instruction = self._pipeline._pipeline[stage]
        private_stage = self.stages[stage]

        private_stage.fields[0].setText(f"Opcode: {str(instruction.opcode)}")
        private_stage.fields[1].setText(f"Computed: {str(instruction.computed)}")

        if stage == 0:
            private_stage.fields[EISA.MAX_INSTRUCTION_FIELDS].setText(f"Stalled: {str(self._pipeline._stalled_fetch)}")

        if stage == 3:
            private_stage.fields[EISA.MAX_INSTRUCTION_FIELDS].setText(f"Stalled: {str(self._pipeline._stalled_memory)}")

        if instruction.opcode == 0:
            return

        decoded = instruction._decoded

        if decoded is None:
            return

        decoded_fields = decoded._fields

        counter = 2
        for i in decoded_fields:
            key = str(i)
            if key == 'opcode' or len(key) == 1:
                continue
            private_stage.fields[counter].setText(f"{key.capitalize()}: {str(decoded[key])}")
            counter += 1

        '''
        self.stages[stage].encoded.setText(f"Encoded: {self._pipeline._pipeline[stage]._encoded}")
        self.stages[stage].opcode.setText(f"Opcode: {self._pipeline._pipeline[stage].opcode}")

        try:
            dest = self._pipeline._pipeline[stage].try_get('dest')
        except DecodeError:
            dest = None

        try:
            src1 = self._pipeline._pipeline[stage].try_get('op1')
        except DecodeError:
            src1 = None

        try:
            src2 = self._pipeline._pipeline[stage].try_get('op2')
        except DecodeError:
            dest = None

        self.stages[stage].reg1.setText(f"Dest: {dest}")
        self.stages[stage].reg2.setText(f"Src1: {src1}")
        self.stages[stage].reg3.setText(f"Src2: {src2}")

        self.stages[stage].op1.setText(f"DestVal: {self._pipeline._registers[dest]}")
        self.stages[stage].op2.setText(f"Op1: {self._pipeline._registers[src1]}")
        self.stages[stage].op3.setText(f"Op2: {self._pipeline._registers[src2]}")

        #self.stages[stage].computed.setText(f"Computed: {self._pipeline._pipeline[stage]._computed}")
        '''
        '''
        self.stages[stage].encoded.setText(f"Encoded: {self._pipeline._pipeline[stage]._encoded}")
        self.stages[stage].opcode.setText(f"Opcode: {self._pipeline._pipeline[stage]._opcode}")
        self.stages[stage].reg1.setText(f"Reg1: {self._pipeline._pipeline[stage].try_get('dest')}")
        self.stages[stage].reg2.setText(f"Reg2: {self._pipeline._pipeline[stage]._regB}")
        self.stages[stage].reg3.setText(f"Reg3: {self._pipeline._pipeline[stage]._regC}")
        self.stages[stage].op1.setText(f"Op1: {self._pipeline._pipeline[stage]._opA}")
        self.stages[stage].op2.setText(f"Op2: {self._pipeline._pipeline[stage]._opB}")
        self.stages[stage].op3.setText(f"Op3: {self._pipeline._pipeline[stage]._opC}")
        self.stages[stage].computed.setText(f"Computed: {self._pipeline._pipeline[stage].computed}")
        '''

    def load_stages(self):
        '''Loads ALL stages of the pipeline into the UI.'''
        for i in range(5):
            self.load_stage(i)

    def update_ram(self):
        for i in range(1, self.memory_group.ram_rows + 1):
            for j in range(1, self.memory_group.ram_cols + 1):
                val = self._memory._RAM[((i - 1) * self.memory_group.ram_cols) + (j - 1)]
                if self._hex:
                    val = hex(val)
                self.memory_group.ram_widget.item(i - 1, j - 1).setText(str(val))

    def update_regs(self):
        for i in range(1, self.memory_group.regs_rows + 1):
            for j in range(1, self.memory_group.regs_cols + 1):
                val = self._pipeline._registers[((i - 1) * self.memory_group.regs_cols) + (j - 1)]
                if self._hex:
                    val = hex(val)
                self.memory_group.regs_widget.item(i - 1, j - 1).setText(str(val))

    def update_cache(self):
        cache = self._pipeline._memory._cache._cache

        for i in range(1, self.memory_group.cache_rows + 1):
            for j in range(1, self.memory_group.cache_cols + 1):
                val = [i for i in cache[((i - 1) * self.memory_group.cache_cols) + (j - 1)]._data]
                if self._hex:
                    for k in range(len(val)):
                        val[k] = hex(val[k])
                self.memory_group.cache_widget.item(i - 1, j - 1).setText(str(val))

    def update_memory(self):
        self.update_ram()
        self.update_regs()
        self.update_cache()

    def hex_toggle(self):
        self._hex = not (self._hex)
        self.update_ui()

    def reinit_pipe_and_memory(self):
        del self._memory
        del self._pipeline

        self._memory = MemorySubsystem(EISA.ADDRESS_SIZE, EISA.CACHE_SIZE, EISA.CACHE_READ_SPEED,
                                       EISA.CACHE_WRITE_SPEED, EISA.RAM_SIZE, EISA.RAM_READ_SPEED, EISA.RAM_WRITE_SPEED)
        self._pipeline = PipeLine(0, [0] * 32, self._memory)

    def load_program_from_file(self):

        try:
            try:
                self.fp.close()
            except AttributeError:
                pass
        except ValueError:
            pass

        filepath = QFileDialog.getOpenFileName(self, 'Hey! Select a File')[0]
        if filepath == '':
            return

        # TODO - retain prior pipeline/memory in load program rather than deleting it

        self.reinit_pipe_and_memory()

        self.fp = open(filepath)

        with self.fp as f:
            content = f.readlines()
        self.program_lines = [x.strip() for x in content]  # Remove whitespace

        for i in range(len(self.program_lines)):
            self._memory._RAM[i] = int(self.program_lines[i], 2)

        self.update_ui()

    def reload_program(self):
        self.reinit_pipe_and_memory()

        try:
            for i in range(len(self.program_lines)):
                self._memory._RAM[i] = int(self.program_lines[i], 2)
            self.update_ui()
        except AttributeError:
            self.error_dialog = QMessageBox().critical(self, "No Program Loaded",
                                                       "Please load a program into EISA before reloading.")

    def load_exchange_demo(self):  # TODO - implement exchange demo
        pass

    def load_matrix_demo(self):  # TODO - implement matrix multiply demo
        self.reinit_pipe_and_memory()

        matrix_fp = "../demos/matrix_multi.expected"

        try:
            self.fp = open(matrix_fp)
        except Exception as e:
            self.error_dialog = QMessageBox().critical(self, "Failed to Load Demo",
                                                       f"The OS reported the following error while trying to load the "
                                                       f"demo:\n {e}")
            try:
                self.fp.close()
            except Exception:
                pass
            return

        with self.fp as f:
            content = f.readlines()
        self.program_lines = [x.strip() for x in content]  # Remove whitespace

        for i in range(len(self.program_lines)):
            self._memory._RAM[i] = int(self.program_lines[i], 2)

        address_counter = 50
        value_counter = 0
        for i in range(5):
            for j in range(5):
                self._memory._RAM[address_counter] = value_counter
                self._memory._RAM[address_counter + 2500] = 24-value_counter
                value_counter += 1
                address_counter += 1

        self.update_ui()


if __name__ == '__main__':
    app = QApplication(sys.argv)

    memory = MemorySubsystem(EISA.ADDRESS_SPACE, EISA.CACHE_SIZE, EISA.CACHE_READ_SPEED, EISA.CACHE_WRITE_SPEED,
                             EISA.RAM_SIZE, EISA.RAM_READ_SPEED, EISA.RAM_WRITE_SPEED)

    # my_pipe = PipeLine(0, [0] * 32, memory)

    my_pipe = PipeLine(0, [i for i in range(EISA.NUM_GP_REGS)], memory)

    # Build UI dialog box
    dlg = Dialog(memory, my_pipe)

    dlg.show()

    try:
        app.exec()
    except Exception as e:
        print(e)
