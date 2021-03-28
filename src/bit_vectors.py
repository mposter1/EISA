from __future__ import annotations # must be first import, allows type hinting of next_device to be the enclosing class
from typing import Dict, List, Type, Optional
from eisa import EISA

class BitVectorField:
    _start: int
    _stop: int
    _size: int

    def __init__(self, start, size):
        self.start = start
        self.size = size
        self.stop = start + size
        self.mask = 2**size - 1


class BitVector:
    _bits: int

    # static variables
    _size: int = EISA.WORD_SIZE
    _fields: Dict[str, BitVectorField] = {}
    _unallocated: List[slice] = [slice(0, _size)]

    def __init__(self):
        self._bits = 0b0

    def __str__(self):
        new_line_char = '\n'
        s = f'raw bits: {self._bits:0{2 + self._size}b}{new_line_char}'
        s += f'{new_line_char.join([f"{cur_key}: {self[cur_key]}" for cur_key in self._fields.keys()])}'
        
        return s

    def __getitem__(self, field: str) -> Optional[int]:
        """gets the value stored at the specified field

        Parameters
        ----------
        field : str
            the name of the field

        Returns
        -------
        int
            the value stored at the field
        None
            if the field does not exist
        """
        target_field = None
        try:
            target_field = self._fields[field]
        except KeyError:
            print(f'\'{field}\' is not a field in type \'{type(self).__name__}\'')
        else:
            return (self._bits >> target_field.start) & target_field.mask

        return None
    
    def __setitem__(self, field: str, value: int) -> None:
        """assigns the passed value to the passed field

        Parameters
        ----------
        field : str
            the name of the field
        value : int
            the value to be assigned

        Raises
        ------
        ValueError
            if the value being assigned will overflow, or if it is negative
        """

        target_field = None
        try:
            target_field = self._fields[field]
        except KeyError:
            print(f'\'{field}\' is not a field in type \'{type(self).__name__}\'')
        else:
            if value > target_field.mask:
                raise ValueError(f'Cannot to assign {value} to \'{field}\'. Can be at most {target_field.mask}')
            elif value < 0:
                raise ValueError(f'Cannot assign negative numbers to \'{field}\'')

            self._bits &= ~(target_field.mask << target_field.start)
            self._bits |= value << target_field.start

    @classmethod
    def add_field(cls, field_name: str, field_start: int, field_size: int) -> Type[BitVector]:
        """creates a new field starting at the passed value, and of the passed size

        Parameters
        ----------
        field_name : str
            the name of the field to be created
        field_start : int
            the first bit of the new field
        field_size : int
            the size, in bits, of the new field to be created

        Returns
        -------
        Type[BitVector]
            itself

        Raises
        ------
        ValueError
            if the parameters of the new field are invalid;
            either they are negative, 
            would extend beyond the size of the bit field, 
            or the bits are already used by another field
        """

        new_field = BitVectorField(field_start, field_size)

        if new_field.start < 0:
            raise(ValueError('Cannot assign a negative to field_start'))

        if cls._size < new_field.stop:
            raise(ValueError('Cannot create a field which extends beyond the bit vector'))

        for i in range(len(cls._unallocated)):
            slot = cls._unallocated[i]
            if slot.start <= new_field.start and new_field.stop <= slot.stop:
                new_unallocated = cls._unallocated[:i]

                if slot.start < new_field.start:
                    new_unallocated.append(slice(slot.start, new_field.start))

                if new_field.stop < slot.stop:
                    new_unallocated.append(slice(slot.stop, new_field.stop))

                new_unallocated += cls._unallocated[i + 1:]

                cls._unallocated = new_unallocated

            cls._fields[field_name] = new_field
            return cls
        
        raise ValueError(f'Cannot create new field \'{field_name}\'. Bits {new_field.start} to {new_field.stop} are already used by another field.')

    @classmethod
    def create_subtype(cls, name: str, size: Optional[int]=None) -> type:
        """creates a new class with the passed name, which inherits from this class

        Parameters
        ----------
        name : str
            the name of the new class to be created
        size : int, optional
            the size , in bits, of the bit vector to be created
            by default None

        Returns
        -------
        type
            the new class that was created
        """
        return type(name, (cls,), {
            '_size'         : size if size is not None else cls._size,
            'add_field'     : cls.add_field
        })